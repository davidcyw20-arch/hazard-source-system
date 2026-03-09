-- Generated from SQLAlchemy models
SET NAMES utf8mb4;


CREATE TABLE alpha_rules (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	gb_version VARCHAR(30) NOT NULL, 
	min_people INTEGER NOT NULL, 
	max_people INTEGER, 
	alpha FLOAT NOT NULL, 
	source VARCHAR(100) NOT NULL, 
	note VARCHAR(255), 
	PRIMARY KEY (id)
)

;


CREATE TABLE category_betas (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	gb_version VARCHAR(30) NOT NULL, 
	category_symbol VARCHAR(20) NOT NULL, 
	beta FLOAT NOT NULL, 
	beta_source VARCHAR(100), 
	source VARCHAR(100) NOT NULL, 
	note VARCHAR(255), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_cat_beta UNIQUE (gb_version, category_symbol)
)

;


CREATE TABLE category_thresholds (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	gb_version VARCHAR(30) NOT NULL, 
	category_symbol VARCHAR(20) NOT NULL, 
	threshold_quantity FLOAT NOT NULL, 
	unit VARCHAR(20) NOT NULL, 
	source VARCHAR(100) NOT NULL, 
	note VARCHAR(255), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_cat_threshold UNIQUE (gb_version, category_symbol)
)

;


CREATE TABLE chemicals (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	gb_version VARCHAR(30) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	category VARCHAR(80), 
	cas_no VARCHAR(50), 
	critical_quantity FLOAT NOT NULL, 
	unit VARCHAR(20) NOT NULL, 
	source_standard VARCHAR(100) NOT NULL, 
	hazard_category_symbol VARCHAR(20), 
	beta FLOAT, 
	beta_source VARCHAR(100), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_chem_name_cas UNIQUE (name, cas_no)
)

;


CREATE TABLE level_rules (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	gb_version VARCHAR(30) NOT NULL, 
	min_r FLOAT NOT NULL, 
	max_r FLOAT, 
	level VARCHAR(20) NOT NULL, 
	source VARCHAR(100) NOT NULL, 
	note VARCHAR(255), 
	PRIMARY KEY (id)
)

;


CREATE TABLE rule_sets (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(120) NOT NULL, 
	is_active BOOL NOT NULL, 
	levels JSON NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;


CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(120), 
	password_hash VARCHAR(255) NOT NULL, 
	`role` VARCHAR(20) NOT NULL, 
	is_active BOOL NOT NULL, 
	company_name VARCHAR(200), 
	contact_name VARCHAR(80), 
	phone VARCHAR(40), 
	address VARCHAR(255), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
)

;


CREATE TABLE audit_logs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	user_id INTEGER, 
	action VARCHAR(80) NOT NULL, 
	detail VARCHAR(500), 
	ip VARCHAR(60), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


CREATE TABLE evaluation_results (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	owner_id INTEGER NOT NULL, 
	enterprise_name VARCHAR(200) NOT NULL, 
	rule_set_id INTEGER NOT NULL, 
	gb_version VARCHAR(30) NOT NULL, 
	s_value FLOAT NOT NULL, 
	exposure_people_500m INTEGER NOT NULL, 
	alpha_used FLOAT NOT NULL, 
	r_value FLOAT NOT NULL, 
	is_major_hazard BOOL NOT NULL, 
	level VARCHAR(20), 
	level_by_gb VARCHAR(20), 
	basis JSON NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	reviewer_id INTEGER, 
	reviewed_at DATETIME, 
	review_remark VARCHAR(255), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id), 
	FOREIGN KEY(rule_set_id) REFERENCES rule_sets (id), 
	FOREIGN KEY(reviewer_id) REFERENCES users (id)
)

;


CREATE TABLE storage_records (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	owner_id INTEGER NOT NULL, 
	enterprise_name VARCHAR(200) NOT NULL, 
	chemical_id INTEGER NOT NULL, 
	amount FLOAT NOT NULL, 
	unit VARCHAR(20) NOT NULL, 
	unit_name VARCHAR(120), 
	unit_type VARCHAR(50), 
	qty_basis VARCHAR(30), 
	material_type VARCHAR(30), 
	mixture_name VARCHAR(120), 
	mixture_category_symbol VARCHAR(20), 
	location VARCHAR(200), 
	storage_method VARCHAR(100), 
	properties VARCHAR(200), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id), 
	FOREIGN KEY(chemical_id) REFERENCES chemicals (id)
)

;

CREATE UNIQUE INDEX ix_users_username ON users (username);
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE INDEX ix_chem_name ON chemicals (name);
CREATE INDEX ix_storage_records_owner_id ON storage_records (owner_id);
CREATE INDEX ix_eval_enterprise ON evaluation_results (enterprise_name);
CREATE INDEX ix_evaluation_results_owner_id ON evaluation_results (owner_id);
CREATE INDEX ix_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX ix_alpha_rules_range ON alpha_rules (min_people, max_people);
CREATE INDEX ix_cat_threshold_symbol ON category_thresholds (category_symbol);
CREATE INDEX ix_cat_beta_symbol ON category_betas (category_symbol);
