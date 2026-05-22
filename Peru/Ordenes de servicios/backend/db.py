"""MariaDB configuration helpers for the future persistence layer.

The live frontend still reads and writes localStorage. These helpers keep the
database contract explicit without requiring a MariaDB driver during preview.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MariaDBConfig:
	host: str
	port: int
	database: str
	user: str
	password: str

	@property
	def is_configured(self) -> bool:
		return all([self.host, self.database, self.user, self.password])


def get_mariadb_config() -> MariaDBConfig:
	return MariaDBConfig(
		host=os.getenv("MCP_MARIADB_HOST", ""),
		port=int(os.getenv("MCP_MARIADB_PORT", "3306")),
		database=os.getenv("MCP_MARIADB_DATABASE", "bdmcperu"),
		user=os.getenv("MCP_MARIADB_USER", ""),
		password=os.getenv("MCP_MARIADB_PASSWORD", ""),
	)
