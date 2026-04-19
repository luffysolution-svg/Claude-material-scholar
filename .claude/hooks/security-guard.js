// Security guard hook for materials research assistant
// Prevents destructive operations on research data files

module.exports = async function securityGuard(context) {
  const { tool, input } = context;

  // Protect data files from accidental deletion/overwrite
  const PROTECTED_PATTERNS = [
    /batch_registry\.json$/,
    /Research\/.*\.(csv|xlsx|xls|txt)$/,
    /\.claude\/skills\/.*\.py$/,
    /\.claude\/agents\/.*\.json$/,
    /00-Hub\.md$/,
  ];

  const PROTECTED_TOOLS = ['Bash'];
  const DANGEROUS_COMMANDS = [
    /rm\s+-rf/,
    /del\s+\/[sf]/i,
    /rmdir\s+\/s/i,
    /git\s+reset\s+--hard/,
    /git\s+clean\s+-f/,
    />\s*batch_registry/,
  ];

  if (tool === 'Bash' && input?.command) {
    for (const pattern of DANGEROUS_COMMANDS) {
      if (pattern.test(input.command)) {
        return {
          block: true,
          message: `⚠️ Security guard blocked potentially destructive command: ${input.command}\nIf intentional, confirm explicitly.`
        };
      }
    }
  }

  if ((tool === 'Write' || tool === 'Edit') && input?.file_path) {
    for (const pattern of PROTECTED_PATTERNS) {
      if (pattern.test(input.file_path)) {
        // Allow writes but log them
        console.error(`[security-guard] Writing to protected file: ${input.file_path}`);
      }
    }
  }

  return { block: false };
};
