-- Migration for Buildings System
-- Add columns to projects table
ALTER TABLE projects ADD COLUMN IF NOT EXISTS total_area FLOAT DEFAULT 0;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS floors_count INTEGER DEFAULT 0;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS steel_factor FLOAT DEFAULT 120;

-- Create unit_templates table
CREATE TABLE IF NOT EXISTS unit_templates (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    area FLOAT DEFAULT 0,
    rooms_count INTEGER DEFAULT 0,
    bathrooms_count INTEGER DEFAULT 0,
    count INTEGER DEFAULT 0,
    project_id VARCHAR(36) NOT NULL REFERENCES projects(id),
    project_name VARCHAR(255) NOT NULL,
    created_by VARCHAR(36) NOT NULL REFERENCES users(id),
    created_by_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_unit_templates_project ON unit_templates(project_id);
CREATE INDEX IF NOT EXISTS idx_unit_templates_code ON unit_templates(code);

-- Create unit_template_materials table
CREATE TABLE IF NOT EXISTS unit_template_materials (
    id VARCHAR(36) PRIMARY KEY,
    template_id VARCHAR(36) NOT NULL REFERENCES unit_templates(id) ON DELETE CASCADE,
    catalog_item_id VARCHAR(36) NOT NULL REFERENCES price_catalog(id),
    item_code VARCHAR(100),
    item_name VARCHAR(255) NOT NULL,
    unit VARCHAR(50) DEFAULT 'قطعة',
    quantity_per_unit FLOAT NOT NULL,
    unit_price FLOAT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_template_materials_template ON unit_template_materials(template_id);
CREATE INDEX IF NOT EXISTS idx_template_materials_catalog ON unit_template_materials(catalog_item_id);

-- Create project_floors table
CREATE TABLE IF NOT EXISTS project_floors (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    floor_number INTEGER NOT NULL,
    floor_name VARCHAR(100),
    area FLOAT DEFAULT 0,
    steel_factor FLOAT DEFAULT 120
);
CREATE INDEX IF NOT EXISTS idx_project_floors_project ON project_floors(project_id);
CREATE INDEX IF NOT EXISTS idx_project_floors_number ON project_floors(project_id, floor_number);

-- Create project_area_materials table
CREATE TABLE IF NOT EXISTS project_area_materials (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    catalog_item_id VARCHAR(36) NOT NULL REFERENCES price_catalog(id),
    item_code VARCHAR(100),
    item_name VARCHAR(255) NOT NULL,
    unit VARCHAR(50) DEFAULT 'طن',
    factor FLOAT DEFAULT 0,
    unit_price FLOAT DEFAULT 0,
    calculation_type VARCHAR(50) DEFAULT 'all_floors',
    selected_floors TEXT,
    tile_width FLOAT DEFAULT 0,
    tile_height FLOAT DEFAULT 0,
    waste_percentage FLOAT DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_area_materials_project ON project_area_materials(project_id);
CREATE INDEX IF NOT EXISTS idx_area_materials_catalog ON project_area_materials(catalog_item_id);

-- Create supply_tracking table
CREATE TABLE IF NOT EXISTS supply_tracking (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    catalog_item_id VARCHAR(36) NOT NULL REFERENCES price_catalog(id),
    item_code VARCHAR(100),
    item_name VARCHAR(255) NOT NULL,
    unit VARCHAR(50) DEFAULT 'قطعة',
    required_quantity FLOAT NOT NULL,
    received_quantity FLOAT DEFAULT 0,
    unit_price FLOAT DEFAULT 0,
    source VARCHAR(50) DEFAULT 'quantity',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_supply_tracking_project ON supply_tracking(project_id);
CREATE INDEX IF NOT EXISTS idx_supply_tracking_catalog ON supply_tracking(catalog_item_id);
