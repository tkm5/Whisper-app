"""ジョブ管理モジュール．"""
from enum import Enum
from typing import TypedDict
import uuid


class JobStatus(Enum):
    """ジョブの状態を表す列挙型．"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(TypedDict, total=False):
    """ジョブ情報の型定義．"""
    id: str
    filename: str
    status: JobStatus
    file_path: str
    result_text: str
    result_path: str


class JobManager:
    """ジョブを管理するクラス．"""

    def __init__(self) -> None:
        """JobManagerを初期化する．"""
        self._jobs: dict[str, Job] = {}

    def create_job(self, filename: str) -> str:
        """新しいジョブを作成する．

        Args:
            filename: アップロードされたファイル名．

        Returns:
            作成されたジョブのID．
        """
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = Job(
            id=job_id,
            filename=filename,
            status=JobStatus.PENDING,
        )
        return job_id

    def get_job(self, job_id: str) -> Job:
        """ジョブ情報を取得する．

        Args:
            job_id: ジョブID．

        Returns:
            ジョブ情報．

        Raises:
            KeyError: ジョブが存在しない場合．
        """
        if job_id not in self._jobs:
            raise KeyError(f"Job not found: {job_id}")
        return self._jobs[job_id]

    def update_status(self, job_id: str, status: JobStatus) -> None:
        """ジョブのステータスを更新する．

        Args:
            job_id: ジョブID．
            status: 新しいステータス．

        Raises:
            KeyError: ジョブが存在しない場合．
        """
        job = self.get_job(job_id)
        self._jobs[job_id] = {**job, "status": status}

    def set_file_path(self, job_id: str, file_path: str) -> None:
        """ジョブにファイルパスを設定する．

        Args:
            job_id: ジョブID．
            file_path: 保存されたファイルのパス．

        Raises:
            KeyError: ジョブが存在しない場合．
        """
        job = self.get_job(job_id)
        self._jobs[job_id] = {**job, "file_path": file_path}

    def set_result(self, job_id: str, result_text: str, result_path: str) -> None:
        """ジョブに結果を設定する．

        Args:
            job_id: ジョブID．
            result_text: 文字起こし結果テキスト．
            result_path: 結果ファイルのパス．

        Raises:
            KeyError: ジョブが存在しない場合．
        """
        job = self.get_job(job_id)
        self._jobs[job_id] = {
            **job,
            "result_text": result_text,
            "result_path": result_path,
            "status": JobStatus.COMPLETED,
        }
