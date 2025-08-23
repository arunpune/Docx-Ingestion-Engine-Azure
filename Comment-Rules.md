# 📝 Comment Rules for Insurance AI Agent Project

This document outlines the standardized commenting rules used throughout the Insurance AI Agent project to ensure consistency, maintainability, and clear authorship attribution.

## 🎯 General Principles

1. **Every file must have author attribution**
2. **Comments should be clear, concise, and meaningful**
3. **Follow language-specific comment conventions**
4. **Include purpose and context for complex logic**

## 📋 Language-Specific Comment Rules

### Python Files (.py)
```python
"""
Module Title/Purpose
====================
Author: Full Name

Brief description of the module's purpose and functionality.

Key Features:
- Feature 1
- Feature 2
- Feature 3
"""
```

### HTML Files (.html)
```html
<!DOCTYPE html>
<!-- Project Name - Template Purpose -->
<!-- Author: Full Name -->
<html lang="en">
```

### Configuration Files (.yml, .env, Dockerfile)
```yaml
# Project Name - Configuration Purpose
# Author: Full Name
```

### JSON Files (.json)
Since JSON doesn't support comments, use a separate AUTHORS.md file or include author info in description fields where possible:
```json
{
  "_comment": "Project Name - Purpose - Author: Full Name"
}
```

### Markdown Files (.md)
```markdown
# Title
<!-- Author: Full Name -->

Content...
```

## 🔧 Standard Comment Templates

### File Header Template
```
Purpose: [Brief description]
Author: [Full Name]
Created: [Date]
Last Modified: [Date]
Dependencies: [Key dependencies]
```

### Function/Method Comments
```python
def function_name(param1: type, param2: type) -> return_type:
    """
    Brief description of what the function does.
    
    Args:
        param1 (type): Description of parameter
        param2 (type): Description of parameter
        
    Returns:
        return_type: Description of return value
        
    Raises:
        ExceptionType: Description of when this exception is raised
    """
```

### Class Comments
```python
class ClassName:
    """
    Brief description of the class purpose.
    
    This class handles [specific functionality] and provides [capabilities].
    
    Attributes:
        attribute1 (type): Description
        attribute2 (type): Description
        
    Example:
        obj = ClassName()
        obj.method()
    """
```

### Complex Logic Comments
```python
# ========== SECTION HEADER ==========
# Clear explanation of what this section does
# and why it's necessary

# Step-by-step explanation for complex algorithms
# 1. First step explanation
# 2. Second step explanation
# 3. Final step explanation
```

## 📁 File Type Specific Rules

### Configuration Files
- Must include author and purpose
- Explain non-obvious configuration choices
- Document environment-specific settings

### Template Files
- Include template purpose and target audience
- Document any dynamic content or variables
- Explain styling choices for CSS

### Logic App JSON Files
- Use separate AUTHORS.md file for attribution
- Document workflow purpose and triggers
- Explain complex logic app steps

### Requirements/Dependencies Files
- Group related dependencies
- Explain version constraints
- Document development vs production dependencies

## ✅ Quality Standards

### Required Elements
- [ ] Author attribution
- [ ] File purpose/description
- [ ] Key dependencies documented
- [ ] Complex logic explained
- [ ] Public APIs documented

### Best Practices
- Use consistent formatting
- Keep comments up-to-date with code changes
- Avoid redundant or obvious comments
- Focus on "why" not just "what"
- Use proper grammar and spelling

## 🚫 What to Avoid

- **Commented-out code** (use version control instead)
- **Obvious comments** (`i++  // increment i`)
- **Outdated comments** that don't match current code
- **Inconsistent formatting** across files
- **Missing author attribution**

## 🔄 Maintenance

- Review comments during code reviews
- Update comments when functionality changes
- Remove obsolete comments promptly
- Ensure new files follow these standards

---

**Note**: These rules ensure our codebase remains maintainable, well-documented, and easily transferable between team members.
