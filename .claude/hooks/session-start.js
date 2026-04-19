// Session start hook for materials research assistant
// Displays project status, recent experiments, batch counts, and available commands

const fs = require('fs');
const path = require('path');

function countFiles(dir, ext) {
  if (!fs.existsSync(dir)) return 0;
  let count = 0;
  function scan(d) {
    try {
      for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
        if (entry.isDirectory()) scan(path.join(d, entry.name));
        else if (!ext || entry.name.endsWith(ext)) count++;
      }
    } catch (e) {}
  }
  scan(dir);
  return count;
}

function getRecentFiles(dir, days = 7) {
  if (!fs.existsSync(dir)) return [];
  const cutoff = Date.now() - days * 24 * 60 * 60 * 1000;
  const results = [];
  function scan(d) {
    try {
      for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
        const fullPath = path.join(d, entry.name);
        if (entry.isDirectory()) scan(fullPath);
        else if (entry.name.endsWith('.md')) {
          const stat = fs.statSync(fullPath);
          if (stat.mtimeMs > cutoff) results.push({ path: fullPath, mtime: stat.mtimeMs });
        }
      }
    } catch (e) {}
  }
  scan(dir);
  return results.sort((a, b) => b.mtime - a.mtime).slice(0, 5);
}

module.exports = async function sessionStart(context) {
  const { cwd } = context;
  const researchDir = path.join(cwd, 'Research');

  console.log('\n╔══════════════════════════════════════════════════════╗');
  console.log('║       Materials Research Assistant                    ║');
  console.log('╚══════════════════════════════════════════════════════╝\n');

  if (!fs.existsSync(researchDir)) {
    console.log('No active research projects found.');
    console.log('Use /materials-init to create a new project.\n');
  } else {
    const projects = fs.readdirSync(researchDir, { withFileTypes: true })
      .filter(d => d.isDirectory() && !d.name.startsWith('.') && d.name !== 'templates')
      .map(d => d.name);

    if (projects.length > 0) {
      console.log(`📁 Active Projects (${projects.length}):`);
      for (const proj of projects) {
        const projDir = path.join(researchDir, proj);
        const papers = countFiles(path.join(projDir, 'Papers'), '.md');
        const chars = countFiles(path.join(projDir, 'Characterization'), '.md');
        const reactions = countFiles(path.join(projDir, 'Reactions'), '.md');

        const hubPath = path.join(projDir, '00-Hub.md');
        let status = 'active';
        if (fs.existsSync(hubPath)) {
          const m = fs.readFileSync(hubPath, 'utf-8').match(/status:\s*(\w+)/);
          if (m) status = m[1];
        }
        console.log(`  • ${proj} [${status}]  Papers:${papers} Char:${chars} Reactions:${reactions}`);
      }
      console.log('');
    }

    // Recent activity
    const recent = getRecentFiles(researchDir, 7);
    if (recent.length > 0) {
      console.log('🕐 Recent (7 days):');
      for (const f of recent) {
        const rel = path.relative(researchDir, f.path);
        const d = new Date(f.mtime).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        console.log(`  ${d}  ${rel}`);
      }
      console.log('');
    }

    // Batch count
    let totalBatches = 0;
    function findRegistries(dir) {
      try {
        for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
          const fp = path.join(dir, entry.name);
          if (entry.isDirectory()) findRegistries(fp);
          else if (entry.name === 'batch_registry.json') {
            try { totalBatches += Object.keys(JSON.parse(fs.readFileSync(fp, 'utf8'))).length; } catch (e) {}
          }
        }
      } catch (e) {}
    }
    findRegistries(researchDir);
    if (totalBatches > 0) console.log(`🧪 Synthesis Batches: ${totalBatches} total\n`);
  }

  console.log('📋 Commands:');
  console.log('  /materials-init      /characterization    /catalysis-results');
  console.log('  /dft-analysis        /synthesis-log       /manuscript-draft   /paper-review\n');
};
