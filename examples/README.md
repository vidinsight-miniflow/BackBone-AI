# Example Schemas

This directory contains example JSON schemas for testing BackBone-AI code generation.

## Available Examples

### 1. Simple Schema (`simple_schema.json`)
A basic schema with a single User table. Great for testing the basic workflow.

**Tables:** Users
**Features:** Timestamps, unique constraints, nullable fields

**Usage:**
```bash
backbone-ai generate --schema examples/simple_schema.json --output ./test_simple
```

### 2. Blog Schema (`blog_schema.json`)
A blog backend with Users, Posts, and Comments tables with relationships.

**Tables:** Users, Posts, Comments
**Features:** Timestamps, soft delete, foreign keys, one-to-many/many-to-one relationships, enums

**Usage:**
```bash
backbone-ai generate --schema examples/blog_schema.json --output ./test_blog
```

### 3. E-commerce Schema (`ecommerce_schema.json`)
A complete e-commerce backend with Products, Orders, Categories, and OrderItems.

**Tables:** Users, Categories, Products, Orders, OrderItems
**Features:** Complex relationships, numeric fields, enums, order tracking, inventory management

**Usage:**
```bash
backbone-ai generate --schema examples/ecommerce_schema.json --output ./test_ecommerce
```

## Schema Structure

All schemas follow this structure:

```json
{
  "project_name": "ProjectName",
  "db_type": "postgresql",
  "description": "Project description",
  "schema": [
    {
      "table_name": "table_name",
      "class_name": "ClassName",
      "options": {
        "use_timestamps": true,
        "use_soft_delete": false
      },
      "columns": [...],
      "relationships": [...]
    }
  ]
}
```

## Testing Validation Only

You can validate a schema without generating code:

```bash
backbone-ai validate --schema examples/blog_schema.json
```

This will:
- Validate JSON structure
- Check foreign key references
- Analyze table dependencies
- Show build order
- Display warnings and errors

## Creating Your Own Schema

1. Copy one of the example schemas
2. Modify the tables, columns, and relationships
3. Validate it first: `backbone-ai validate --schema your_schema.json`
4. Generate code: `backbone-ai generate --schema your_schema.json --output ./output`

## Supported Column Types

- `Integer` - Integer values
- `String` - Variable length strings (requires `length`)
- `Text` - Long text fields
- `Boolean` - True/false values
- `Numeric` - Decimal numbers (requires `precision` and `scale`)
- `ForeignKey` - Foreign key reference (requires `target`)
- `Enum` - Enumeration (requires `values` array)
- `DateTime` - Date and time
- `Date` - Date only
- `JSON` - JSON data

## Relationship Types

- `one_to_many` - One record has many related records
- `many_to_one` - Many records relate to one record
- `one_to_one` - One-to-one relationship
- `many_to_many` - Many-to-many relationship (requires junction table)

## Options

### Table Options

- `use_timestamps` (bool) - Add created_at/updated_at columns
- `use_soft_delete` (bool) - Add is_deleted/deleted_at columns

### Column Options

- `primary_key` (bool) - Mark as primary key
- `unique` (bool) - Add unique constraint
- `nullable` (bool) - Allow NULL values
- `default` - Default value
- `index` (bool) - Add database index
- `length` (int) - String length (for String type)
- `precision` (int) - Numeric precision (for Numeric type)
- `scale` (int) - Numeric scale (for Numeric type)
