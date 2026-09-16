"""Build-time policy for UniCoreFW's generated public API declarations.

This module is intentionally dependency-free. Public, module-owned functions
are discovered by :mod:`scripts.generate_core_registry`; only non-function
exports and compatibility decisions remain explicit here.
"""

PUBLIC_MODULES_IN_ORDER = (
    "array",
    "object",
    "function",
    "utils",
    "types",
    "security",
    "regex_policy",
    "string",
    "crypto",
    "template",
    "orm",
    "db",
    "supporter",
)

PUBLIC_SUBMODULES = frozenset(
    """
    array core crypto db function object orm regex_policy security string
    supporter template types utils
    """.split()  # noqa: SIM905
)

CORE_MODULES_IN_ORDER = (
    "array",
    "object",
    "string",
    "function",
    "utils",
    "types",
    "security",
    "template",
)

# Database and ORM modules are parsed from source so registry generation does
# not import optional backends or initialize their module-level capability
# detection. Their public functions remain lazy, static compatibility calls.
SOURCE_DISCOVERY_MODULES = frozenset(("db", "orm", "supporter"))

LAZY_CHAIN_MODULES = ("crypto",)
LAZY_STATIC_MODULES = ("db", "orm")

CORE_COMPATIBILITY_ALIASES = (
    ("max", "utils", "max_value", True),
    ("min", "utils", "min_value", True),
)

# Exact ownership is deliberate. Any new or changed collision fails generation
# until its compatibility semantics have been reviewed explicitly.
APPROVED_PUBLIC_NAME_COLLISIONS = {
    "filter_": ("object", "function"),
    "invoke": ("object", "function"),
    "map_": ("object", "function"),
    "max_value": ("array", "utils"),
    "min_value": ("array", "utils"),
    "now": ("function", "utils"),
    "reduce_": ("object", "function"),
    "update": ("object", "orm"),
}

# These names are classes, constants, imported compatibility objects, or
# backend-provided callables. Module-owned public functions are intentionally
# absent: the generator discovers them automatically.
EXPLICIT_PUBLIC_EXPORTS_BY_MODULE = {
    "security": frozenset(
        """
        AuditLogger AuthorizationError DistributedRateLimiter
        InputValidationError LocalRateLimiter RateLimitBackend RateLimiter
        RedisRateLimitBackend ResourceLimitError SanitizationError SecurityError
        """.split()  # noqa: SIM905
    ),
    "regex_policy": frozenset(("RegexLimits", "UnsafeRegex")),
    "crypto": frozenset(
        (
            "CRYPTO_AVAILABLE",
            "CryptoUnavailableError",
            "InvalidKey",
            "InvalidToken",
        )
    ),
    "template": frozenset(("TemplateLimits",)),
    "orm": frozenset(
        """
        ARRAY AsyncEngine AsyncSession Base Boolean CheckConstraint Column Date
        DateTime Enum Float ForeignKey Index Integer JSON LargeBinary Numeric
        ORMUnavailableError Session String Text Time UniqueConstraint and_ asc
        async_sessionmaker bindparam create_async_engine delete desc func insert
        or_ relationship select selectinload sessionmaker text update
        """.split()  # noqa: SIM905
    ),
    "db": frozenset(
        """
        BackupRestore CacheManager ConnectionError ConnectionPool DataExporter
        DataImporter Database DatabaseConnectionError DatabaseError
        DatabaseImportError EXCEL_AVAILABLE ExportError ImportError
        MONGODB_AVAILABLE MYSQL_AVAILABLE Migration PANDAS_AVAILABLE
        POSTGRES_AVAILABLE QueryBuilder QueryError REDIS_AVAILABLE UnsafeCSS
        UnsafeSQL
        """.split()  # noqa: SIM905
    ),
}
