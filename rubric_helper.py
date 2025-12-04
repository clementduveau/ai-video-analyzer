#!/usr/bin/env python3
"""
Rubric Helper Script

Interactive tool for creating, validating, and managing evaluation rubrics.
Supports both hierarchical rubrics (with categories and nested criteria) and
legacy flat rubrics (with direct criteria).

Usage:
    python rubric_helper.py create    # Create a new rubric interactively
    python rubric_helper.py validate <filename>  # Validate a rubric file
    python rubric_helper.py list      # List all available rubrics
    python rubric_helper.py show <name>  # Show details of a rubric
    python rubric_helper.py edit <name>  # Edit an existing rubric
    python rubric_helper.py versions <name>  # List all versions of a rubric
    python rubric_helper.py restore <name> <version>  # Restore rubric to version

Versioning:
- Automatic backups are created when editing rubrics
- Versions are auto-incremented when editing (e.g., 1.0 → 1.1)
- Backups are stored in rubrics/versions/ with timestamps
- Use 'versions' command to see available versions
- Use 'restore' command to revert to a previous version

New hierarchical format:
- Rubrics have categories with nested criteria
- Point-based scoring instead of weighted 1-10 scale
- Includes rubric_id and version fields for versioning
- Backward compatible with old flat format rubrics

Examples:
    # Create a new hierarchical rubric
    python rubric_helper.py create

    # Edit a rubric (creates backup and increments version)
    python rubric_helper.py edit sales-demo

    # View all versions of a rubric
    python rubric_helper.py versions sales-demo

    # Restore to a previous version
    python rubric_helper.py restore sales-demo 1.0
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional


def validate_rubric(rubric: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate rubric structure and return (is_valid, error_message).

    Supports both old format (flat criteria) and new format (hierarchical categories).
    Returns:
        Tuple of (True, None) if valid, or (False, error_message) if invalid
    """
    # Check if this is new format (categories) or old format (criteria)
    is_new_format = "categories" in rubric
    is_old_format = "criteria" in rubric

    if not is_new_format and not is_old_format:
        return False, "Rubric must have either 'categories' (new format) or 'criteria' (old format)"

    if is_new_format:
        # Validate new hierarchical format
        required_keys = {"categories", "scale", "overall_method", "thresholds"}
        if not all(key in rubric for key in required_keys):
            missing = required_keys - set(rubric.keys())
            return False, f"Missing required keys: {missing}"

        # Validate categories
        if not isinstance(rubric["categories"], list) or len(rubric["categories"]) == 0:
            return False, "categories must be a non-empty list"

        seen_cat_ids = set()
        total_weight = 0.0
        for i, category in enumerate(rubric["categories"]):
            # Check required fields
            required_fields = {"category_id", "label", "weight", "max_points", "criteria"}
            if not all(field in category for field in required_fields):
                missing = required_fields - set(category.keys())
                return False, f"Category {i} missing required fields: {missing}"

            # Check for duplicate category IDs
            if category["category_id"] in seen_cat_ids:
                return False, f"Duplicate category ID: {category['category_id']}"
            seen_cat_ids.add(category["category_id"])

            # Check weight is a number
            try:
                weight = float(category["weight"])
                if weight < 0 or weight > 1:
                    return False, f"Category '{category['category_id']}' weight must be between 0 and 1"
                total_weight += weight
            except (TypeError, ValueError):
                return False, f"Category '{category['category_id']}' weight must be a number"

            # Check max_points is positive
            try:
                max_points = int(category["max_points"])
                if max_points <= 0:
                    return False, f"Category '{category['category_id']}' max_points must be positive"
            except (TypeError, ValueError):
                return False, f"Category '{category['category_id']}' max_points must be a positive integer"

            # Validate criteria within category
            if not isinstance(category["criteria"], list) or len(category["criteria"]) == 0:
                return False, f"Category '{category['category_id']}' criteria must be a non-empty list"

            seen_crit_ids = set()
            category_points = 0
            for j, criterion in enumerate(category["criteria"]):
                # Check required fields
                required_crit_fields = {"criterion_id", "label", "desc", "max_points"}
                if not all(field in criterion for field in required_crit_fields):
                    missing = required_crit_fields - set(criterion.keys())
                    return False, f"Category '{category['category_id']}' criterion {j} missing required fields: {missing}"

                # Check for duplicate criterion IDs within category
                if criterion["criterion_id"] in seen_crit_ids:
                    return False, f"Duplicate criterion ID in category '{category['category_id']}': {criterion['criterion_id']}"
                seen_crit_ids.add(criterion["criterion_id"])

                # Check max_points is positive
                try:
                    crit_max_points = int(criterion["max_points"])
                    if crit_max_points <= 0:
                        return False, f"Criterion '{criterion['criterion_id']}' max_points must be positive"
                    category_points += crit_max_points
                except (TypeError, ValueError):
                    return False, f"Criterion '{criterion['criterion_id']}' max_points must be a positive integer"

            # Check category points match sum of criteria points
            if category_points != category["max_points"]:
                return False, f"Category '{category['category_id']}' max_points ({category['max_points']}) doesn't match sum of criteria points ({category_points})"

        # Check category weights sum to approximately 1.0
        if not (0.99 <= total_weight <= 1.01):
            return False, f"Category weights must sum to 1.0 (current sum: {total_weight:.4f})"

    else:
        # Validate old flat format
        required_keys = {"criteria", "scale", "overall_method", "thresholds"}
        if not all(key in rubric for key in required_keys):
            missing = required_keys - set(rubric.keys())
            return False, f"Missing required keys: {missing}"

        # Validate criteria
        if not isinstance(rubric["criteria"], list) or len(rubric["criteria"]) == 0:
            return False, "criteria must be a non-empty list"

        seen_ids = set()
        total_weight = 0.0
        for i, criterion in enumerate(rubric["criteria"]):
            # Check required fields
            required_fields = {"id", "label", "desc", "weight"}
            if not all(field in criterion for field in required_fields):
                missing = required_fields - set(criterion.keys())
                return False, f"Criterion {i} missing required fields: {missing}"

            # Check for duplicate IDs
            if criterion["id"] in seen_ids:
                return False, f"Duplicate criterion ID: {criterion['id']}"
            seen_ids.add(criterion["id"])

            # Check weight is a number
            try:
                weight = float(criterion["weight"])
                if weight < 0 or weight > 1:
                    return False, f"Criterion '{criterion['id']}' weight must be between 0 and 1"
                total_weight += weight
            except (TypeError, ValueError):
                return False, f"Criterion '{criterion['id']}' weight must be a number"

        # Check weights sum to approximately 1.0 (allow small floating point errors)
        if not (0.99 <= total_weight <= 1.01):
            return False, f"Criterion weights must sum to 1.0 (current sum: {total_weight:.4f})"

    # Validate scale (common to both formats)
    if not isinstance(rubric["scale"], dict):
        return False, "scale must be a dict"
    if "min" not in rubric["scale"] or "max" not in rubric["scale"]:
        return False, "scale must have 'min' and 'max' keys"
    try:
        min_val = float(rubric["scale"]["min"])
        max_val = float(rubric["scale"]["max"])
        if min_val >= max_val:
            return False, "scale min must be less than max"
    except (TypeError, ValueError):
        return False, "scale min and max must be numbers"

    # Validate thresholds (common to both formats)
    if not isinstance(rubric["thresholds"], dict):
        return False, "thresholds must be a dict"
    if "pass" not in rubric["thresholds"] or "revise" not in rubric["thresholds"]:
        return False, "thresholds must have 'pass' and 'revise' keys"
    try:
        pass_threshold = float(rubric["thresholds"]["pass"])
        revise_threshold = float(rubric["thresholds"]["revise"])
        if revise_threshold >= pass_threshold:
            return False, "revise threshold must be less than pass threshold"
    except (TypeError, ValueError):
        return False, "thresholds must be numbers"

    return True, None


def get_rubrics_dir() -> Path:
    """Get the rubrics directory path."""
    return Path(__file__).parent / "rubrics"


def load_rubric_from_file(filename: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Load a rubric from file, return (rubric, error_message)."""
    rubrics_dir = get_rubrics_dir()
    rubric_path = rubrics_dir / f"{filename}.json"

    if not rubric_path.exists():
        return None, f"Rubric file not found: {rubric_path}"

    try:
        with open(rubric_path, 'r') as f:
            rubric = json.load(f)
        return rubric, None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {rubric_path}: {e}"
    except Exception as e:
        return None, f"Error loading {rubric_path}: {e}"


def save_rubric_to_file(rubric: Dict[str, Any], filename: str, create_backup: bool = True) -> Tuple[bool, Optional[str]]:
    """Save a rubric to file, return (success, error_message)."""
    rubrics_dir = get_rubrics_dir()
    rubrics_dir.mkdir(exist_ok=True)

    rubric_path = rubrics_dir / f"{filename}.json"

    # Create backup if file exists and backup is requested
    if create_backup and rubric_path.exists():
        try:
            # Create versions directory if it doesn't exist
            versions_dir = rubrics_dir / "versions"
            versions_dir.mkdir(exist_ok=True)

            # Get current timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Load current rubric to get version info
            try:
                with open(rubric_path, 'r') as f:
                    current_rubric = json.load(f)
                current_version = current_rubric.get('version', '1.0')
            except:
                current_version = 'unknown'

            # Create backup filename
            backup_filename = f"{filename}.v{current_version}.{timestamp}.json"
            backup_path = versions_dir / backup_filename

            # Copy current file to backup
            import shutil
            shutil.copy2(rubric_path, backup_path)
            
            # Mark the backup as archived
            try:
                with open(backup_path, 'r') as f:
                    backup_rubric = json.load(f)
                backup_rubric['status'] = 'archive'
                with open(backup_path, 'w') as f:
                    json.dump(backup_rubric, f, indent=2)
                print(f"💾 Backup created: {backup_filename} (status: archive)")
            except Exception as e:
                print(f"⚠️  Warning: Could not mark backup as archived: {e}")

        except Exception as e:
            print(f"⚠️  Warning: Could not create backup: {e}")

    try:
        with open(rubric_path, 'w') as f:
            json.dump(rubric, f, indent=2)
        return True, None
    except Exception as e:
        return False, f"Error saving to {rubric_path}: {e}"


def increment_version(current_version: str) -> str:
    """Increment a version string (e.g., '1.0' -> '1.1', '2.5' -> '2.6')."""
    try:
        # Split version into parts
        parts = current_version.split('.')
        if len(parts) >= 2:
            # Increment minor version
            major = parts[0]
            minor = str(int(parts[1]) + 1)
            return f"{major}.{minor}"
        else:
            # If no minor version, add .1
            return f"{current_version}.1"
    except (ValueError, IndexError):
        # If parsing fails, append .1
        return f"{current_version}.1"


def list_available_rubrics() -> List[Dict[str, str]]:
    """List all available rubrics in the rubrics directory."""
    rubrics_dir = get_rubrics_dir()
    available = []

    if rubrics_dir.exists():
        for rubric_file in sorted(rubrics_dir.glob("*.json")):
            try:
                with open(rubric_file, 'r') as f:
                    rubric_data = json.load(f)

                # Validate before adding to list
                is_valid, _ = validate_rubric(rubric_data)
                # Only include rubrics marked as current
                if is_valid and rubric_data.get('status') == 'current':
                    available.append({
                        'filename': rubric_file.stem,
                        'name': rubric_data.get('name', rubric_file.stem),
                        'description': rubric_data.get('description', 'No description available')
                    })
            except (json.JSONDecodeError, Exception):
                continue

    # Ensure sample rubric is always available
    if not any(r['filename'] == 'sample-rubric' for r in available):
        available.insert(0, {
            'filename': 'sample-rubric',
            'name': 'Sample Rubric',
            'description': 'Built-in sample rubric'
        })

    return available


def list_rubric_versions(filename: str) -> List[Dict[str, str]]:
    """List all versions of a rubric."""
    rubrics_dir = get_rubrics_dir()
    versions_dir = rubrics_dir / "versions"

    # Remove .json extension if present
    if filename.endswith('.json'):
        filename = filename[:-5]

    versions = []

    # Add current version if it exists
    current_path = rubrics_dir / f"{filename}.json"
    if current_path.exists():
        try:
            with open(current_path, 'r') as f:
                rubric = json.load(f)
            versions.append({
                'version': rubric.get('version', '1.0'),
                'filename': f"{filename}.json",
                'type': 'current',
                'timestamp': 'current'
            })
        except:
            pass

    # Add backup versions
    if versions_dir.exists():
        for backup_file in sorted(versions_dir.glob(f"{filename}.v*.json"), reverse=True):
            try:
                # Parse version and timestamp from filename
                # Format: filename.v{major}.{minor}.{timestamp}.json
                parts = backup_file.stem.split('.')
                if len(parts) >= 4 and parts[1].startswith('v'):
                    version_part = parts[1][1:]  # Remove 'v' prefix from parts[1] (major version)
                    minor_version = parts[2]     # parts[2] is minor version
                    timestamp = parts[3]         # parts[3] is timestamp
                    
                    # Construct version string
                    version = f"{version_part}.{minor_version}"
                    
                    versions.append({
                        'version': version,
                        'filename': backup_file.name,
                        'type': 'backup',
                        'timestamp': timestamp
                    })
            except:
                continue

    return versions


def restore_rubric_version(filename: str, version: str) -> Tuple[bool, Optional[str]]:
    """Restore a rubric to a specific version."""
    rubrics_dir = get_rubrics_dir()
    versions_dir = rubrics_dir / "versions"

    # Find the backup file for this version
    backup_path = None
    for backup_file in versions_dir.glob(f"{filename}.v{version}.*.json"):
        backup_path = backup_file
        break

    if not backup_path:
        return False, f"No backup found for version {version}"

    # Load the backup
    try:
        with open(backup_path, 'r') as f:
            rubric = json.load(f)
    except Exception as e:
        return False, f"Error loading backup: {e}"

    # Ensure the restored rubric has current status
    rubric['status'] = 'current'

    # Save as current version (without creating another backup)
    current_path = rubrics_dir / f"{filename}.json"
    try:
        with open(current_path, 'w') as f:
            json.dump(rubric, f, indent=2)
        return True, None
    except Exception as e:
        return False, f"Error restoring: {e}"


def create_rubric_interactive() -> Dict[str, Any]:
    """Create a new rubric interactively using the new hierarchical format."""
    print("🎯 Creating a new evaluation rubric (hierarchical format)")
    print("=" * 60)

    # Basic info
    name = input("Rubric name: ").strip()
    while not name:
        name = input("Rubric name (required): ").strip()

    description = input("Description: ").strip()
    while not description:
        description = input("Description (required): ").strip()

    rubric_id = input("Rubric ID (unique identifier, e.g., 'custom-demo'): ").strip().lower().replace(' ', '-')
    while not rubric_id:
        rubric_id = input("Rubric ID (required): ").strip().lower().replace(' ', '-')

    version = input("Version (default: 1.0): ").strip() or "1.0"

    # Scale (now point-based)
    print("\n📏 Scoring Scale (point-based)")
    try:
        max_score = int(input("Maximum total score (default: 50): ") or "50")
        if max_score <= 0:
            print("❌ Maximum score must be positive. Using default (50).")
            max_score = 50
    except ValueError:
        print("❌ Invalid number. Using default (50).")
        max_score = 50

    # Thresholds (now point-based)
    print("\n🎯 Pass/Fail Thresholds (point-based)")
    try:
        pass_threshold = int(input(f"Pass threshold (≥ this score, default: {int(max_score * 0.7)}): ") or str(int(max_score * 0.7)))
        revise_threshold = int(input(f"Revise threshold (≥ this score, default: {int(max_score * 0.5)}): ") or str(int(max_score * 0.5)))

        if revise_threshold >= pass_threshold:
            print("❌ Revise threshold must be less than pass threshold. Using defaults.")
            pass_threshold = int(max_score * 0.7)
            revise_threshold = int(max_score * 0.5)
    except ValueError:
        print("❌ Invalid numbers. Using defaults.")
        pass_threshold = int(max_score * 0.7)
        revise_threshold = int(max_score * 0.5)

    # Categories (hierarchical structure)
    print("\n� Evaluation Categories")
    print("Create categories with nested criteria. Each category needs:")
    print("- Category ID (unique identifier, e.g., 'content_quality')")
    print("- Category Label (display name, e.g., 'Content Quality')")
    print("- Category Weight (importance, 0.0-1.0, total must sum to 1.0)")
    print("- Category Max Points (total points for this category)")
    print("- Nested Criteria (evaluation items within the category)")

    categories = []
    total_weight = 0.0

    while True:
        print(f"\nCategory #{len(categories) + 1}")
        print("-" * 30)

        # Category ID
        category_id = input("Category ID (e.g., content_quality): ").strip().lower().replace(' ', '_')
        while not category_id or not category_id.replace('_', '').isalnum():
            category_id = input("Category ID (letters/numbers/underscores only): ").strip().lower().replace(' ', '_')

        # Check for duplicate category IDs
        if any(c['category_id'] == category_id for c in categories):
            print(f"❌ Category ID '{category_id}' already exists. Choose a different ID.")
            continue

        # Category Label
        category_label = input("Category Label (display name): ").strip()
        while not category_label:
            category_label = input("Category Label (required): ").strip()

        # Category Weight
        while True:
            try:
                category_weight = float(input("Category Weight (0.0-1.0): ").strip())
                if 0 <= category_weight <= 1:
                    if total_weight + category_weight > 1.01:
                        remaining = 1.0 - total_weight
                        print(f"⚠️  Total weight would exceed 1.0. Remaining weight: {remaining:.3f}")
                        if input("Continue anyway? (y/N): ").lower().startswith('y'):
                            break
                        else:
                            continue
                    break
                else:
                    print("❌ Weight must be between 0.0 and 1.0")
            except ValueError:
                print("❌ Please enter a valid number")

        # Category Max Points
        while True:
            try:
                category_max_points = int(input("Category Max Points: ").strip())
                if category_max_points > 0:
                    break
                else:
                    print("❌ Max points must be positive")
            except ValueError:
                print("❌ Please enter a valid number")

        # Add criteria for this category
        criteria = []
        criteria_total_points = 0
        print(f"\nAdding criteria for category '{category_label}'")
        
        while True:
            print(f"\n  Criterion #{len(criteria) + 1} for {category_label}")
            print("  " + "-" * 20)

            # Criterion ID
            criterion_id = input("  Criterion ID (e.g., technical_accuracy): ").strip().lower().replace(' ', '_')
            while not criterion_id or not criterion_id.replace('_', '').isalnum():
                criterion_id = input("  Criterion ID (letters/numbers/underscores only): ").strip().lower().replace(' ', '_')

            # Check for duplicate criterion IDs within this category
            if any(c['criterion_id'] == criterion_id for c in criteria):
                print(f"❌ Criterion ID '{criterion_id}' already exists in this category.")
                continue

            # Criterion Label
            crit_label = input("  Criterion Label: ").strip()
            while not crit_label:
                crit_label = input("  Criterion Label (required): ").strip()

            # Criterion Description
            crit_desc = input("  Criterion Description: ").strip()
            while not crit_desc:
                crit_desc = input("  Criterion Description (required): ").strip()

            # Criterion Max Points
            while True:
                try:
                    crit_max_points = int(input("  Criterion Max Points: ").strip())
                    if crit_max_points > 0:
                        break
                    else:
                        print("❌ Max points must be positive")
                except ValueError:
                    print("❌ Please enter a valid number")

            criteria.append({
                'criterion_id': criterion_id,
                'label': crit_label,
                'desc': crit_desc,
                'max_points': crit_max_points
            })

            criteria_total_points += crit_max_points
            print(f"✓ Added criterion. Category points so far: {criteria_total_points}")

            if input("\n  Add another criterion to this category? (Y/n): ").lower().startswith('n'):
                break

        # Check if criteria points match category max points
        if criteria_total_points != category_max_points:
            print(f"⚠️  Category max points ({category_max_points}) doesn't match sum of criteria points ({criteria_total_points})")
            if not input("Continue anyway? (y/N): ").lower().startswith('y'):
                print("❌ Category creation cancelled.")
                continue

        categories.append({
            'category_id': category_id,
            'label': category_label,
            'weight': category_weight,
            'max_points': category_max_points,
            'criteria': criteria
        })

        total_weight += category_weight
        print(f"✓ Added category. Total weight so far: {total_weight:.3f}")

        if total_weight >= 0.99:
            print("🎉 Total weight is approximately 1.0. No more categories needed.")
            break

        if input("\nAdd another category? (Y/n): ").lower().startswith('n'):
            break

    # Check final weight
    if not (0.99 <= total_weight <= 1.01):
        print(f"\n⚠️  Warning: Total weight is {total_weight:.3f}, should be 1.0")
        if not input("Continue anyway? (y/N): ").lower().startswith('y'):
            print("❌ Rubric creation cancelled.")
            sys.exit(1)

    # Create the rubric in new format
    rubric = {
        'rubric_id': rubric_id,
        'version': version,
        'status': 'current',
        'name': name,
        'description': description,
        'categories': categories,
        'scale': {
            'min': 0,
            'max': max_score
        },
        'overall_method': 'total_points',
        'thresholds': {
            'pass': pass_threshold,
            'revise': revise_threshold
        }
    }

    return rubric


def show_rubric_details(rubric: Dict[str, Any]):
    """Display detailed information about a rubric."""
    print(f"📋 {rubric['name']}")
    print("=" * 50)
    print(f"Description: {rubric['description']}")
    
    # Check if new format (has categories) or old format (has criteria)
    is_new_format = "categories" in rubric
    
    if is_new_format:
        print(f"Version: {rubric.get('version', '1.0')}")
        print(f"Rubric ID: {rubric.get('rubric_id', 'unknown')}")
    
    print(f"Scale: {rubric['scale']['min']}-{rubric['scale']['max']}")
    print(f"Overall Method: {rubric['overall_method']}")
    print(f"Pass Threshold: ≥{rubric['thresholds']['pass']}")
    print(f"Revise Threshold: ≥{rubric['thresholds']['revise']}")

    if is_new_format:
        # New format: categories with nested criteria
        total_categories = len(rubric['categories'])
        total_criteria = sum(len(cat['criteria']) for cat in rubric['categories'])
        print(f"\n� Categories ({total_categories}) with Criteria ({total_criteria} total):")
        print("-" * 50)
        
        for cat in rubric['categories']:
            cat_name = cat['label']
            cat_id = cat['category_id']
            cat_weight = cat.get('weight', 0) * 100
            cat_max_points = cat['max_points']
            
            print(f"📂 {cat_name} ({cat_id})")
            print(f"   Weight: {cat_weight:.1f}% | Max Points: {cat_max_points}")
            print(f"   Criteria:")
            
            for criterion in cat['criteria']:
                crit_name = criterion['label']
                crit_id = criterion['criterion_id']
                crit_max_points = criterion['max_points']
                crit_desc = criterion.get('desc', '')
                
                print(f"     • {crit_name} ({crit_id}) - {crit_max_points} points")
                if crit_desc:
                    print(f"       {crit_desc}")
            print()
    else:
        # Old format: flat criteria array
        print(f"\n�📊 Criteria ({len(rubric['criteria'])} total):")
        print("-" * 50)

        total_weight = 0.0
        for i, criterion in enumerate(rubric['criteria'], 1):
            weight_pct = criterion['weight'] * 100
            print(f"{i}. {criterion['label']} ({criterion['id']})")
            print(f"   Weight: {weight_pct:.1f}%")
            print(f"   Description: {criterion['desc']}")
            print()
            total_weight += criterion['weight']

        print(f"Total Weight: {total_weight:.3f} (should be 1.0)")


def edit_rubric_interactive(filename: str):
    """Edit an existing rubric interactively."""
    rubric, error = load_rubric_from_file(filename)
    if error:
        print(f"❌ Error loading rubric: {error}")
        return

    if rubric is None:
        print(f"❌ Rubric '{filename}' not found.")
        return

    print(f"📝 Editing rubric: {rubric['name']}")
    print("=" * 50)

    # Show current details
    show_rubric_details(rubric)

    # Check if new format (has categories) or old format (has criteria)
    is_new_format = "categories" in rubric

    print("\n🔧 What would you like to edit?")
    if is_new_format:
        print("1. Basic info (name, description, version)")
        print("2. Scale and thresholds")
        print("3. Add a new category")
        print("4. Edit existing categories/criteria")
        print("5. Remove a category")
        print("6. Cancel")
    else:
        print("1. Basic info (name, description)")
        print("2. Scale and thresholds")
        print("3. Add a new criterion")
        print("4. Edit existing criteria")
        print("5. Remove a criterion")
        print("6. Cancel")

    choice = input("\nChoice (1-6): ").strip()

    if choice == '1':
        # Edit basic info
        print("\n📝 Editing basic information")
        new_name = input(f"Name [{rubric['name']}]: ").strip()
        if new_name:
            rubric['name'] = new_name

        new_desc = input(f"Description [{rubric['description']}]: ").strip()
        if new_desc:
            rubric['description'] = new_desc

        if is_new_format:
            new_version = input(f"Version [{rubric.get('version', '1.0')}]: ").strip()
            if new_version:
                rubric['version'] = new_version

    elif choice == '2':
        # Edit scale and thresholds
        print("\n📏 Editing scale and thresholds")
        try:
            min_val = input(f"Min score [{rubric['scale']['min']}]: ").strip()
            if min_val:
                rubric['scale']['min'] = int(min_val)

            max_val = input(f"Max score [{rubric['scale']['max']}]: ").strip()
            if max_val:
                rubric['scale']['max'] = int(max_val)

            pass_thresh = input(f"Pass threshold [{rubric['thresholds']['pass']}]: ").strip()
            if pass_thresh:
                rubric['thresholds']['pass'] = int(pass_thresh)

            revise_thresh = input(f"Revise threshold [{rubric['thresholds']['revise']}]: ").strip()
            if revise_thresh:
                rubric['thresholds']['revise'] = int(revise_thresh)

        except ValueError as e:
            print(f"❌ Invalid input: {e}")
            return

    elif choice == '3':
        if is_new_format:
            # Add new category
            print("\n➕ Adding new category")
            category_id = input("Category ID (e.g., content_quality): ").strip().lower().replace(' ', '_')
            while not category_id or not category_id.replace('_', '').isalnum():
                category_id = input("Category ID (letters/numbers/underscores only): ").strip().lower().replace(' ', '_')

            if any(c['category_id'] == category_id for c in rubric['categories']):
                print(f"❌ Category ID '{category_id}' already exists.")
                return

            label = input("Category Label (display name): ").strip()
            while not label:
                label = input("Category Label (required): ").strip()

            try:
                weight = float(input("Category Weight (0.0-1.0): ").strip())
                if not (0 <= weight <= 1):
                    print("❌ Weight must be between 0.0 and 1.0")
                    return
            except ValueError:
                print("❌ Invalid weight")
                return

            try:
                max_points = int(input("Category Max Points: ").strip())
                if max_points <= 0:
                    print("❌ Max points must be positive")
                    return
            except ValueError:
                print("❌ Invalid max points")
                return

            # Add criteria for this category
            criteria = []
            print(f"\nAdding criteria for category '{label}'")
            while True:
                criterion_id = input("Criterion ID (e.g., technical_accuracy): ").strip().lower().replace(' ', '_')
                while not criterion_id or not criterion_id.replace('_', '').isalnum():
                    criterion_id = input("Criterion ID (letters/numbers/underscores only): ").strip().lower().replace(' ', '_')

                if any(c['criterion_id'] == criterion_id for c in criteria):
                    print(f"❌ Criterion ID '{criterion_id}' already exists in this category.")
                    continue

                crit_label = input("Criterion Label: ").strip()
                while not crit_label:
                    crit_label = input("Criterion Label (required): ").strip()

                crit_desc = input("Criterion Description: ").strip()
                while not crit_desc:
                    crit_desc = input("Criterion Description (required): ").strip()

                try:
                    crit_max_points = int(input("Criterion Max Points: ").strip())
                    if crit_max_points <= 0:
                        print("❌ Max points must be positive")
                        continue
                except ValueError:
                    print("❌ Invalid max points")
                    continue

                criteria.append({
                    'criterion_id': criterion_id,
                    'label': crit_label,
                    'desc': crit_desc,
                    'max_points': crit_max_points
                })

                if input("Add another criterion to this category? (Y/n): ").lower().startswith('n'):
                    break

            rubric['categories'].append({
                'category_id': category_id,
                'label': label,
                'weight': weight,
                'max_points': max_points,
                'criteria': criteria
            })
        else:
            # Add new criterion (old format)
            print("\n➕ Adding new criterion")
            criterion_id = input("ID: ").strip().lower().replace(' ', '_')
            if any(c['id'] == criterion_id for c in rubric['criteria']):
                print(f"❌ ID '{criterion_id}' already exists.")
                return

            label = input("Label: ").strip()
            desc = input("Description: ").strip()

            try:
                weight = float(input("Weight (0.0-1.0): ").strip())
                if not (0 <= weight <= 1):
                    print("❌ Weight must be between 0.0 and 1.0")
                    return
            except ValueError:
                print("❌ Invalid weight")
                return

            rubric['criteria'].append({
                'id': criterion_id,
                'label': label,
                'desc': desc,
                'weight': weight
            })

    elif choice == '4':
        if is_new_format:
            # Edit existing categories/criteria
            print("\n📝 Editing existing categories and criteria")
            for i, category in enumerate(rubric['categories'], 1):
                print(f"{i}. {category['label']} ({category['category_id']}) - {len(category['criteria'])} criteria")

            try:
                cat_idx = int(input("\nCategory number to edit: ").strip()) - 1
                if not (0 <= cat_idx < len(rubric['categories'])):
                    print("❌ Invalid category number")
                    return
            except ValueError:
                print("❌ Invalid number")
                return

            category = rubric['categories'][cat_idx]
            print(f"\nEditing Category: {category['label']}")

            # Edit category details
            new_label = input(f"Category Label [{category['label']}]: ").strip()
            if new_label:
                category['label'] = new_label

            try:
                new_weight = input(f"Category Weight [{category['weight']}]: ").strip()
                if new_weight:
                    category['weight'] = float(new_weight)
            except ValueError:
                print("❌ Invalid weight")

            try:
                new_max_points = input(f"Category Max Points [{category['max_points']}]: ").strip()
                if new_max_points:
                    category['max_points'] = int(new_max_points)
            except ValueError:
                print("❌ Invalid max points")

            # Edit criteria within this category
            print(f"\nCriteria in '{category['label']}' category:")
            for j, criterion in enumerate(category['criteria'], 1):
                print(f"  {j}. {criterion['label']} ({criterion['criterion_id']}) - {criterion['max_points']} points")

            crit_choice = input("\nEdit a criterion? (number or 'n' to skip): ").strip()
            if crit_choice.isdigit():
                try:
                    crit_idx = int(crit_choice) - 1
                    if 0 <= crit_idx < len(category['criteria']):
                        criterion = category['criteria'][crit_idx]
                        print(f"\nEditing Criterion: {criterion['label']}")

                        new_crit_label = input(f"Criterion Label [{criterion['label']}]: ").strip()
                        if new_crit_label:
                            criterion['label'] = new_crit_label

                        new_crit_desc = input(f"Criterion Description [{criterion.get('desc', '')}]: ").strip()
                        if new_crit_desc:
                            criterion['desc'] = new_crit_desc

                        try:
                            new_crit_max_points = input(f"Criterion Max Points [{criterion['max_points']}]: ").strip()
                            if new_crit_max_points:
                                criterion['max_points'] = int(new_crit_max_points)
                        except ValueError:
                            print("❌ Invalid max points")
                except ValueError:
                    print("❌ Invalid criterion number")
        else:
            # Edit existing criteria (old format)
            print("\n📝 Editing existing criteria")
            for i, criterion in enumerate(rubric['criteria'], 1):
                print(f"{i}. {criterion['label']} ({criterion['id']}) - {criterion['weight']:.3f}")

            try:
                idx = int(input("\nCriterion number to edit: ").strip()) - 1
                if not (0 <= idx < len(rubric['criteria'])):
                    print("❌ Invalid criterion number")
                    return
            except ValueError:
                print("❌ Invalid number")
                return

            criterion = rubric['criteria'][idx]
            print(f"\nEditing: {criterion['label']}")

            new_label = input(f"Label [{criterion['label']}]: ").strip()
            if new_label:
                criterion['label'] = new_label

            new_desc = input(f"Description [{criterion['desc']}]: ").strip()
            if new_desc:
                criterion['desc'] = new_desc

            try:
                new_weight = input(f"Weight [{criterion['weight']}]: ").strip()
                if new_weight:
                    criterion['weight'] = float(new_weight)
            except ValueError:
                print("❌ Invalid weight")

    elif choice == '5':
        if is_new_format:
            # Remove category
            print("\n🗑️ Removing category")
            for i, category in enumerate(rubric['categories'], 1):
                print(f"{i}. {category['label']} ({category['category_id']}) - {len(category['criteria'])} criteria")

            try:
                idx = int(input("\nCategory number to remove: ").strip()) - 1
                if not (0 <= idx < len(rubric['categories'])):
                    print("❌ Invalid category number")
                    return
            except ValueError:
                print("❌ Invalid number")
                return

            removed = rubric['categories'].pop(idx)
            print(f"✓ Removed category: {removed['label']}")
        else:
            # Remove criterion (old format)
            print("\n🗑️ Removing criterion")
            for i, criterion in enumerate(rubric['criteria'], 1):
                print(f"{i}. {criterion['label']} ({criterion['id']}) - {criterion['weight']:.3f}")

            try:
                idx = int(input("\nCriterion number to remove: ").strip()) - 1
                if not (0 <= idx < len(rubric['criteria'])):
                    print("❌ Invalid criterion number")
                    return
            except ValueError:
                print("❌ Invalid number")
                return

            removed = rubric['criteria'].pop(idx)
            print(f"✓ Removed: {removed['label']}")

    elif choice == '6':
        print("❌ Edit cancelled.")
        return
    else:
        print("❌ Invalid choice.")
        return

    # Validate the edited rubric
    is_valid, error = validate_rubric(rubric)
    if not is_valid:
        print(f"❌ Validation failed: {error}")
        print("Changes not saved.")
        return

    # Auto-increment version for new-format rubrics
    if is_new_format:
        current_version = rubric.get('version', '1.0')
        new_version = increment_version(current_version)
        rubric['version'] = new_version
        print(f"📈 Version incremented: {current_version} → {new_version}")

    # Save the changes
    success, error = save_rubric_to_file(rubric, filename)
    if success:
        print(f"✓ Rubric '{filename}' updated successfully!")
    else:
        print(f"❌ Error saving rubric: {error}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'create':
        rubric = create_rubric_interactive()

        # Validate
        is_valid, error = validate_rubric(rubric)
        if not is_valid:
            print(f"❌ Validation failed: {error}")
            sys.exit(1)

        # Get filename
        filename = input("\n💾 Filename (without .json): ").strip()
        while not filename:
            filename = input("Filename (required): ").strip()

        # Save
        success, error = save_rubric_to_file(rubric, filename)
        if success:
            print(f"✓ Rubric saved as '{filename}.json'")
            print("\nTo use this rubric:")
            print(f"  CLI: python cli/evaluate_video.py --rubric {filename} <video>")
            print(f"  Code: VideoEvaluator(rubric_name='{filename}')")
        else:
            print(f"❌ Error saving: {error}")

    elif command == 'validate':
        if len(sys.argv) < 3:
            print("❌ Usage: python rubric_helper.py validate <filename>")
            sys.exit(1)

        filename = sys.argv[2]
        
        # Handle both relative paths and filenames
        if filename.startswith('rubrics/'):
            # Remove rubrics/ prefix if present
            filename = filename[8:]  # Remove 'rubrics/' prefix
        
        if not filename.endswith('.json'):
            filename += '.json'

        rubric_path = get_rubrics_dir() / filename

        try:
            with open(rubric_path, 'r') as f:
                rubric = json.load(f)
        except FileNotFoundError:
            print(f"❌ File not found: {rubric_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            sys.exit(1)

        is_valid, error = validate_rubric(rubric)
        if is_valid:
            print(f"✓ Rubric '{filename}' is valid!")
        else:
            print(f"❌ Rubric '{filename}' is invalid:")
            print(f"   {error}")
            sys.exit(1)

    elif command == 'list':
        rubrics = list_available_rubrics()
        if not rubrics:
            print("❌ No rubrics found.")
            sys.exit(1)

        print("📋 Available Rubrics:")
        print("=" * 50)
        for rubric in rubrics:
            print(f"• {rubric['filename']}: {rubric['name']}")
            print(f"  {rubric['description']}")
            print()

    elif command == 'show':
        if len(sys.argv) < 3:
            print("❌ Usage: python rubric_helper.py show <rubric_name>")
            sys.exit(1)

        rubric_name = sys.argv[2]
        rubric, error = load_rubric_from_file(rubric_name)
        if error:
            print(f"❌ Error: {error}")
            sys.exit(1)

        if rubric is None:
            print(f"❌ Rubric '{rubric_name}' not found.")
            sys.exit(1)

        show_rubric_details(rubric)

    elif command == 'edit':
        if len(sys.argv) < 3:
            print("❌ Usage: python rubric_helper.py edit <rubric_name>")
            sys.exit(1)

        rubric_name = sys.argv[2]
        edit_rubric_interactive(rubric_name)

    elif command == 'versions':
        if len(sys.argv) < 3:
            print("❌ Usage: python rubric_helper.py versions <rubric_name>")
            sys.exit(1)

        rubric_name = sys.argv[2]
        versions = list_rubric_versions(rubric_name)

        if not versions:
            print(f"❌ No versions found for rubric '{rubric_name}'.")
            sys.exit(1)

        print(f"📋 Versions for rubric '{rubric_name}':")
        print("=" * 60)
        for version in versions:
            type_indicator = "📄" if version['type'] == 'current' else "💾"
            timestamp_info = "" if version['type'] == 'current' else f" ({version['timestamp']})"
            print(f"{type_indicator} Version {version['version']}{timestamp_info}")
            print(f"   File: {version['filename']}")
            print()

    elif command == 'restore':
        if len(sys.argv) < 4:
            print("❌ Usage: python rubric_helper.py restore <rubric_name> <version>")
            sys.exit(1)

        rubric_name = sys.argv[2]
        version = sys.argv[3]

        success, error = restore_rubric_version(rubric_name, version)
        if success:
            print(f"✓ Rubric '{rubric_name}' restored to version {version}!")
        else:
            print(f"❌ Error restoring rubric: {error}")
            sys.exit(1)

    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()