"""
批量优化模块 - 更高效的批量处理
"""

import os
import json
import time
import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BatchTask:
    """批量任务"""
    id: int
    prompt: str
    status: str = "pending"  # pending, processing, completed, failed
    output_path: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self):
        self.tasks: List[BatchTask] = []
        self.output_dir = None
        self.on_progress: Optional[Callable] = None
    
    def load_from_file(self, file_path: str) -> List[BatchTask]:
        """从文件加载任务"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            self.tasks = []
            for i, line in enumerate(lines, 1):
                self.tasks.append(BatchTask(id=i, prompt=line))
            
            logger.info(f"加载 {len(self.tasks)} 个任务")
            return self.tasks
            
        except Exception as e:
            logger.error(f"加载任务文件失败: {e}")
            return []
    
    def load_from_list(self, prompts: List[str]) -> List[BatchTask]:
        """从列表加载任务"""
        self.tasks = []
        for i, prompt in enumerate(prompts, 1):
            self.tasks.append(BatchTask(id=i, prompt=prompt))
        return self.tasks
    
    def process(
        self,
        generate_func: Callable,
        output_dir: str,
        resume: bool = True
    ) -> Dict:
        """
        处理批量任务
        
        Args:
            generate_func: 生成函数，接受 prompt，返回 output_path
            output_dir: 输出目录
            resume: 是否跳过已完成的任务
            
        Returns:
            处理结果统计
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 加载进度
        progress_file = os.path.join(output_dir, "batch_progress.json")
        if resume and os.path.exists(progress_file):
            self._load_progress(progress_file)
        
        # 统计
        total = len(self.tasks)
        success = 0
        failed = 0
        skipped = 0
        total_time = 0
        
        print(f"\n{'='*50}")
        print(f"  批量处理开始")
        print(f"  共 {total} 个任务")
        print(f"{'='*50}\n")
        
        for task in self.tasks:
            # 跳过已完成的任务
            if resume and task.status == "completed":
                skipped += 1
                continue
            
            # 处理任务
            task.status = "processing"
            task.start_time = time.time()
            
            print(f"[{task.id}/{total}] {task.prompt[:50]}...")
            
            try:
                output_path = generate_func(task.prompt)
                if output_path:
                    task.status = "completed"
                    task.output_path = output_path
                    success += 1
                else:
                    task.status = "failed"
                    task.error = "生成失败"
                    failed += 1
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                failed += 1
                logger.error(f"任务 {task.id} 失败: {e}")
            
            task.end_time = time.time()
            total_time += (task.end_time - task.start_time) if task.start_time else 0
            
            # 保存进度
            self._save_progress(progress_file)
            
            # 回调
            if self.on_progress:
                self.on_progress(task, success, failed, total)
        
        # 统计
        result = {
            "total": total,
            "success": success,
            "failed": failed,
            "skipped": skipped,
            "total_time": total_time,
            "avg_time": total_time / max(success, 1)
        }
        
        print(f"\n{'='*50}")
        print(f"  批量处理完成")
        print(f"  成功: {success}/{total}")
        print(f"  失败: {failed}")
        print(f"  跳过: {skipped}")
        print(f"  总耗时: {total_time:.1f}s")
        print(f"  平均耗时: {result['avg_time']:.1f}s/张")
        print(f"{'='*50}")
        
        return result
    
    def _save_progress(self, progress_file: str):
        """保存进度"""
        try:
            progress = [asdict(task) for task in self.tasks]
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存进度失败: {e}")
    
    def _load_progress(self, progress_file: str):
        """加载进度"""
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            
            # 更新任务状态
            for p in progress:
                for task in self.tasks:
                    if task.id == p.get('id'):
                        task.status = p.get('status', 'pending')
                        task.output_path = p.get('output_path')
                        task.error = p.get('error')
                        break
            
            completed = sum(1 for t in self.tasks if t.status == "completed")
            logger.info(f"加载进度: {completed}/{len(self.tasks)} 已完成")
            
        except Exception as e:
            logger.error(f"加载进度失败: {e}")
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == "completed")
        failed = sum(1 for t in self.tasks if t.status == "failed")
        pending = sum(1 for t in self.tasks if t.status == "pending")
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "progress": completed / max(total, 1) * 100
        }
    
    def reset(self):
        """重置所有任务"""
        for task in self.tasks:
            task.status = "pending"
            task.output_path = None
            task.error = None
            task.start_time = None
            task.end_time = None


# 全局实例
batch_processor = BatchProcessor()
