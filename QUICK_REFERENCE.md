# 🚀 Code Intelligence Dashboard - Quick Reference

## ⚡ **Instant Setup**

```bash
# 1. Install dependencies (from main project)
cd /path/to/USASpendingv4
pip install --upgrade --force-reinstall -e ".[enhanced,dev,test,docs]"

# 2. Setup database (from dashboard directory)
cd code-intelligence-dashboard
python -c "from pathlib import Path; from db.populate_db import DatabasePopulator; dp = DatabasePopulator('code_intelligence.db'); dp.create_tables(); dp.populate_from_directory(Path('../src')); print('Ready!')"

# 3. Launch dashboard
python -m panel serve dashboard/app.py --show --autoreload --port 5007 --allow-websocket-origin=localhost:5007
```

**Dashboard URL**: <http://localhost:5007>

## 📁 **Key Files**

| File | Purpose | When to Edit |
|------|---------|--------------|
| `dashboard/app.py` | Main entry point | Adding new tabs, global config |
| `db/populate_db.py` | Analysis engine | New analysis features, metrics |
| `models/types.py` | Data models | Schema changes, validation rules |
| `dashboard/tabs/*.py` | UI components | UI enhancements, new features |

## 🗄️ **Database Quick Commands**

```python
# Check database status
import sqlite3
conn = sqlite3.connect('code_intelligence.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM files'); print(f'Files: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM classes'); print(f'Classes: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM functions'); print(f'Functions: {cursor.fetchone()[0]}')
conn.close()

# Repopulate database
from pathlib import Path
from db.populate_db import DatabasePopulator
dp = DatabasePopulator('code_intelligence.db')
dp.create_tables()
dp.populate_from_directory(Path('../src'))
```

## 🎯 **Common Tasks**

### **Add New Analysis Metric**

1. Update `models/types.py` with new field
2. Modify `db/populate_db.py` AST analysis
3. Update dashboard UI in relevant tab
4. Test with validation suite

### **Add New Dashboard Tab**

1. Create new file in `dashboard/tabs/`
2. Import and add to `dashboard/app.py`
3. Follow existing tab patterns
4. Add filtering/search as needed

### **Debug Issues**

- **Dashboard not loading**: Check database exists and has data
- **No data showing**: Verify database population completed
- **Performance issues**: Check file count, add pagination
- **UI problems**: Check browser console, Panel logs

## 🔧 **Development Commands**

```bash
# Code quality
black dashboard/ db/ models/
mypy dashboard/ db/ models/
isort dashboard/ db/ models/

# Testing
python tests/validation.py
pytest tests/ -v

# Performance profiling
python -m cProfile dashboard/app.py

# Debug mode
python -m panel serve dashboard/app.py --show --autoreload --port 5007 --allow-websocket-origin=localhost:5007 --log-level debug
```

## 📊 **Current Status**

- ✅ **257 files** analyzed from USASpending v4 project
- ✅ **809 classes** detected with full metadata
- ✅ **2,319 functions** analyzed with complexity metrics
- ✅ **All dashboard tabs** functional and interactive
- ✅ **Production ready** with comprehensive documentation

## 🚀 **Next Steps for New Developer**

1. **Get Familiar**: Run the dashboard, explore all tabs
2. **Understand Architecture**: Review `HANDOFF_DOCUMENTATION.md`
3. **Pick Enhancement**: Choose from roadmap in documentation
4. **Start Small**: Add export functionality or new filters
5. **Scale Up**: Advanced visualizations, performance optimization

## 📚 **Essential Resources**

- **Panel Docs**: <https://panel.holoviz.org/>
- **Pydantic Docs**: <https://docs.pydantic.dev/>
- **Python AST**: <https://docs.python.org/3/library/ast.html>
- **Project Docs**: `README.md`, `HANDOFF_DOCUMENTATION.md`

---

**🎯 The dashboard is production-ready. Focus on enhancements and new features!**
