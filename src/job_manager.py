"""ジョブ管理モジュール．"""
import uuid
from enum import Enum
from typing import TypedDict


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

    def get_job(self, job_id: str) -> Job | None:
        """ジョブ情報を取得する．

        Args:
            job_id: ジョブID．

        Returns:
            ジョブ情報．存在しない場合はNone．
        """
        return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        file_path: str | None = None,
        result_text: str | None = None,
        result_path: str | None = None,
    ) -> None:
        """ジョブを更新する．

        Args:
            job_id: ジョブID．
            status: 新しいステータス．
            file_path: 保存されたファイルのパス．
            result_text: 文字起こし結果テキスト．
            result_path: 結果ファイルのパス．

        Raises:
            KeyError: ジョブが存在しない場合．
        """
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job not found: {job_id}")

        updates: dict = {}
        if status is not None:
            updates["status"] = status
        if file_path is not None:
            updates["file_path"] = file_path
        if result_text is not None:
            updates["result_text"] = result_text
        if result_path is not None:
            updates["result_path"] = result_path

        self._jobs[job_id] = {**job, **updates}
