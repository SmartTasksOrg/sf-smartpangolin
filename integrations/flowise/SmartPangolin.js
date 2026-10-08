// Flowise custom node for SmartPangolin (IAIso governance).
// Copy this folder into Flowise's components/nodes/ (or load as a custom tool).
// It shells out to the shipped adapter.py, so sf-smartpangolin must be importable
// (install SmartPangolin from a clone: python -m pip install . ; it is not on PyPI yet)
// or PYTHONPATH set to the repo src/.
const path = require('path');
const { spawnSync } = require('child_process');

class SmartPangolin_Node {
  constructor() {
    this.label = 'SmartPangolin';
    this.name = 'smartpangolin_scan';
    this.version = 1.0;
    this.type = 'SmartPangolin';
    this.category = 'SmartTasks / IAIso Governance';
    this.description = "Scan a project tree for secrets in paths and content before sharing it with an LLM or third party.";
    this.baseClasses = [this.type, 'Tool'];
    this.inputs = [
      { label: 'Input (dir)', name: 'input', type: 'string' },
      { label: 'Python', name: 'python', type: 'string', default: 'python3', optional: true },
    ];
  }

  async init(nodeData) {
    const input = (nodeData.inputs && nodeData.inputs.input) || '';
    const py = (nodeData.inputs && nodeData.inputs.python) || 'python3';
    const adapter = path.join(__dirname, '..', 'adapter.py');
    const res = spawnSync(py, [adapter, '--root', input], { encoding: 'utf8' });
    if (res.status !== 0) throw new Error(res.stderr || 'SmartPangolin adapter failed');
    return JSON.parse(res.stdout);
  }
}

module.exports = { nodeClass: SmartPangolin_Node };
