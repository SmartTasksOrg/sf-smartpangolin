// GENERATED from spec/policy.json by tools/export_policy.py — do not edit.
public final class Policy {
  public static final String VERSION = "2026-08-01.1";
  public static final PathRule[] PATH = {
    new PathRule("SEC-PATH-ENV", new String[]{".env",".env.*","*.env"}),
    new PathRule("SEC-PATH-PEM", new String[]{"*.pem","*.key","*.p8","*.pkcs8","*.pkcs12"}),
    new PathRule("SEC-PATH-PFX", new String[]{"*.pfx","*.p12","*.jks","*.keystore","*.bks"}),
    new PathRule("SEC-PATH-SSH", new String[]{"id_rsa","id_dsa","id_ecdsa","id_ed25519","*.ppk","authorized_keys","known_hosts"}),
    new PathRule("SEC-PATH-NETRC", new String[]{".netrc","_netrc",".git-credentials",".pypirc",".npmrc",".dockercfg"}),
    new PathRule("SEC-PATH-CLOUD", new String[]{"credentials","credentials.json","client_secret*.json","service-account*.json","gcloud-*.json","*serviceaccount*.json","azureauth.json"}),
    new PathRule("SEC-PATH-KUBE", new String[]{"kubeconfig","*.kubeconfig","admin.conf"}),
    new PathRule("SEC-PATH-VAULT", new String[]{"*.kdbx","*.kdb","*.opvault","*.agilekeychain",".vault-token","*.gpg","secring.*"}),
    new PathRule("SEC-PATH-TFSTATE", new String[]{"*.tfstate","*.tfstate.backup","*.tfvars"}),
    new PathRule("SEC-PATH-HISTORY", new String[]{".bash_history",".zsh_history",".psql_history",".mysql_history",".python_history","ConsoleHost_history.txt"}),
    new PathRule("SEC-PATH-DBDUMP", new String[]{"*.sql","*.dump","*.sqlite","*.sqlite3","*.db"})
  };
  public static final String[] DIRS = {".aws",".azure",".docker",".git",".gnupg",".hg",".kube",".mypy_cache",".next",".pytest_cache",".secret",".secrets",".ssh",".svn",".terraform",".tox",".venv","__pycache__","build","dist","env","ft-venv","node_modules","site-packages","venv"};
  public static final Rule[] CONTENT = {
    new Rule("SEC-CONT-HF", "\\bhf_[A-Za-z0-9]{34}\\b"),
    new Rule("SEC-CONT-AWSKEY", "\\b(?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\\b"),
    new Rule("SEC-CONT-AWSSEC", "(?i)aws_secret_access_key\\s*[=:]\\s*[\\\"']?[A-Za-z0-9/+=]{40}"),
    new Rule("SEC-CONT-GHPAT", "\\bgh[pousr]_[A-Za-z0-9]{36}\\b"),
    new Rule("SEC-CONT-GHFINE", "\\bgithub_pat_[A-Za-z0-9_]{60,}\\b"),
    new Rule("SEC-CONT-GITLAB", "\\bglpat-[A-Za-z0-9_\\-]{20}\\b"),
    new Rule("SEC-CONT-ANTHROPIC", "\\bsk-ant-[A-Za-z0-9_\\-]{24,}\\b"),
    new Rule("SEC-CONT-OPENAI", "\\bsk-(?!ant-)(?:proj-)?[A-Za-z0-9_\\-]{32,}\\b"),
    new Rule("SEC-CONT-SLACK", "\\bxox[baprse]-[A-Za-z0-9\\-]{10,}\\b"),
    new Rule("SEC-CONT-GOOGLE", "\\bAIza[0-9A-Za-z_\\-]{35}\\b"),
    new Rule("SEC-CONT-STRIPE", "\\b[rs]k_(?:live|test)_[A-Za-z0-9]{24,}\\b"),
    new Rule("SEC-CONT-NPM", "\\bnpm_[A-Za-z0-9]{36}\\b"),
    new Rule("SEC-CONT-PYPI", "\\bpypi-AgEIcHlwaS5vcmc[A-Za-z0-9_\\-]{50,}\\b"),
    new Rule("SEC-CONT-TELEGRAM", "\\b\\d{8,10}:AA[A-Za-z0-9_\\-]{33}\\b"),
    new Rule("SEC-CONT-SENDGRID", "\\bSG\\.[A-Za-z0-9_\\-]{22}\\.[A-Za-z0-9_\\-]{43}\\b"),
    new Rule("SEC-CONT-PEM", "-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
    new Rule("SEC-CONT-PUTTY", "PuTTY-User-Key-File-\\d"),
    new Rule("SEC-CONT-JWT", "\\beyJ[A-Za-z0-9_\\-]{10,}\\.eyJ[A-Za-z0-9_\\-]{10,}\\.[A-Za-z0-9_\\-]{10,}\\b"),
    new Rule("SEC-CONT-DOCKERAUTH", "\\\"auths\\\"\\s*:\\s*\\{"),
    new Rule("SEC-CONT-CONNSTR", "(?i)\\b(?:postgres(?:ql)?|mysql|mongodb(?:\\+srv)?|redis|amqp|mssql)://[^\\s:@/\\\"']+:[^\\s:@/\\\"']+@"),
    new Rule("SEC-CONT-ASSIGN", "(?i)\\b(?:api[_\\-]?key|secret[_\\-]?key|access[_\\-]?token|auth[_\\-]?token|client[_\\-]?secret|private[_\\-]?key|passwd|password|bearer[_\\-]?token)\\b\\s*[:=]\\s*[\\\"'][^\\\"'\\n]{8,}[\\\"']")
  };
  public static final Rule[] LOCAL = {
    new Rule("LOC-RFC1918", "\\b(?:10\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}|192\\.168\\.\\d{1,3}\\.\\d{1,3}|172\\.(?:1[6-9]|2\\d|3[01])\\.\\d{1,3}\\.\\d{1,3})\\b"),
    new Rule("LOC-CGNAT", "\\b100\\.(?:6[4-9]|[7-9]\\d|1[01]\\d|12[0-7])\\.\\d{1,3}\\.\\d{1,3}\\b"),
    new Rule("LOC-IPV6ULA", "\\bfd[0-9a-f]{2}:(?:[0-9a-f]{0,4}:){1,6}[0-9a-f]{0,4}\\b"),
    new Rule("LOC-UNC", "\\\\\\\\[A-Za-z0-9][A-Za-z0-9._\\-]{1,62}\\\\"),
    new Rule("LOC-WINUSER", "[A-Za-z]:\\\\Users\\\\[^\\\\\\s\\\"'<>|]+"),
    new Rule("LOC-NIXUSER", "/(?:home|Users)/(?!runner\\b|user\\b|ubuntu\\b)[A-Za-z0-9._\\-]+/"),
    new Rule("LOC-INTHOST", "\\b[a-z0-9][a-z0-9\\-]{0,62}\\.(?:local|lan|internal|intranet|corp|home|arpa)\\b"),
    new Rule("LOC-MAC", "\\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\\b"),
    new Rule("LOC-SSHCFG", "(?m)^\\s*HostName\\s+\\S+")
  };
  public static final Rule[] PII = {
    new Rule("PII-EMAIL", "\\b[A-Za-z0-9._%+\\-]+@[A-Za-z0-9.\\-]+\\.[A-Za-z]{2,}\\b"),
    new Rule("PII-SSN", "\\b\\d{3}-\\d{2}-\\d{4}\\b"),
    new Rule("PII-CC", "\\b\\d(?:[ \\-]?\\d){14,15}\\b"),
    new Rule("PII-PHONE", "\\b(?:\\+?\\d{1,3}[ .\\-]?)?(?:\\(\\d{3}\\)|\\d{3})[ .\\-]?\\d{3}[ .\\-]?\\d{4}\\b")
  };
  public static final String AUTHOR = "(?i)(?:^|[^a-z])(authors?|maintainer|maintained by|copyright|\\(c\\)|©|@author)";
  public static final String[] ALLOW = {".env.example",".env.sample",".env.template","env.example"};
  public static final class PathRule { public final String id; public final String[] globs; public PathRule(String i,String[] g){id=i;globs=g;} }
  public static final class Rule { public final String id; public final String regex; public Rule(String i,String r){id=i;regex=r;} }
}
