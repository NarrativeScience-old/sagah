"""Contains Saga class"""

import asyncio
import itertools
import logging
from typing import Any, Callable, List, Optional
from uuid import uuid4

logger = logging.getLogger("sagah")


class SagaFailed(Exception):
    """Raised when a saga fails"""

    def __init__(self, transaction: "SagaTransaction") -> None:
        """Initializes the SagaFailed exception

        Args:
            transaction: Saga transaction that failed

        """
        self.transaction = transaction
        self.message = "Saga failed"


class SagaTransaction:
    """Class representing a single local transaction within a saga"""

    def __init__(
        self, saga_id: str, action: Callable, compensator: Callable, name: str
    ) -> None:
        """Initialize the transaction

        Args:
            saga_id: Saga identifier
            action: Function that represents the desired action
            compensator: Function that is used to compensenate, or rollback, the action
            name: Name to identify the action

        """
        self.saga_id = saga_id
        self.action = action
        self.compensator = compensator
        self.name = name

    def __str__(self) -> str:
        """String representation of the SagaTransaction"""
        return f'{self.__class__.__name__}(name="{self.name}")'

    def _log(self, message: str, level: str = "INFO") -> None:
        """Log a message for the transaction

        Args:
            message: Log message
            level: Log level

        """
        logger.log(
            getattr(logging, level), f"[saga={self.saga_id}] [tx={self.name}] {message}"
        )

    async def call_action(self) -> Any:
        """Call the action function

        Returns:
            action result

        """
        self._log("Saga transaction starting")
        try:
            result = (
                await self.action()
                if asyncio.iscoroutinefunction(self.action)
                else self.action()
            )
            self._log("Saga transaction succeeded")
            return result
        except Exception as e:
            self._log(f"Saga transaction failed: {str(e)}", "ERROR")
            raise

    async def call_compensator(self) -> None:
        """Call the compensator function"""
        self._log("Saga transaction rolling back")
        await self.compensator() if asyncio.iscoroutinefunction(
            self.compensator
        ) else self.compensator()


class Saga:
    """Context manager that implements a saga"""

    def __init__(self, saga_id: Optional[str] = None) -> None:
        """Initializes the Saga

        Args:
            saga_id: Optional saga identifier

        """
        self.saga_id = saga_id or str(uuid4())
        # List of completed transactions for rolling back
        self._transactions: List[SagaTransaction] = []
        # Counter for generating an integer sequence for naming actions
        self._counter = itertools.count(start=1)

    def _log(self, message: str, level: str = "INFO") -> None:
        """Log a message for the saga

        Args:
            message: Log message
            level: Log level

        """
        logger.log(getattr(logging, level), f"[saga={self.saga_id}] {message}")

    def __enter__(self) -> "Saga":
        """Entering the context returns the saga"""
        self._log("Entering saga")
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        """Exiting the saga is a no-op"""
        self._log("Exiting saga")

    async def rollback(self) -> None:
        """Rollback all local transactions in reverse order

        This calls each transaction's compensator function.
        """
        self._log("Rolling back saga transactions")
        while self._transactions:
            tx = self._transactions.pop()
            try:
                await tx.call_compensator()
            except Exception:
                self._transactions.append(tx)
                raise

    async def action(
        self, action: Callable, compensator: Callable, name: Optional[str] = None
    ) -> Any:
        """Trigger an action

        If the action succeeds, register the transaction for a potential rollback in the
        future.

        Args:
            action: Function that represents the desired action
            compensator: Function that is used to compensenate, or rollback, the action
            name: Optional name to identify the action. Will default to
                auto-incrementing integer.

        Raises:
            :py:exc:`SagaFailed`: if the action fails

        Returns:
            result of the action, if it succeeds

        """
        if not name:
            name = str(next(self._counter))

        tx = SagaTransaction(self.saga_id, action, compensator, name)

        try:
            result = await tx.call_action()
        except Exception as e:
            await self.rollback()
            raise SagaFailed(tx) from e
        else:
            self._transactions.append(tx)
            return result
