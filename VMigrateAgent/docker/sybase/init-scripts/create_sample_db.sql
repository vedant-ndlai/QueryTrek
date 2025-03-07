-- Create a sample database for testing
USE master
GO

-- Drop database if it exists
IF EXISTS (SELECT 1 FROM sysdatabases WHERE name = 'SampleDB')
BEGIN
    DROP DATABASE SampleDB
END
GO

-- Create the sample database
CREATE DATABASE SampleDB ON default DEVICE = 'master' = '100M'
GO

USE SampleDB
GO

-- Create schemas
EXEC sp_addgroup 'sales'
GO
EXEC sp_addgroup 'hr'
GO
EXEC sp_addgroup 'inventory'
GO

-- Create tables in sales schema
CREATE TABLE sales.customers (
    customer_id INT IDENTITY PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    address VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
)
GO

CREATE TABLE sales.orders (
    order_id INT IDENTITY PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATETIME DEFAULT GETDATE(),
    status VARCHAR(20) DEFAULT 'pending',
    total_amount DECIMAL(10, 2) DEFAULT 0,
    shipping_address VARCHAR(200),
    shipping_city VARCHAR(50),
    shipping_state VARCHAR(50),
    shipping_zip_code VARCHAR(20),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (customer_id) REFERENCES sales.customers(customer_id)
)
GO

CREATE TABLE inventory.products (
    product_id INT IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sku VARCHAR(50) UNIQUE,
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2),
    stock_quantity INT DEFAULT 0,
    category VARCHAR(50),
    supplier_id INT,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
)
GO

CREATE TABLE sales.order_items (
    order_item_id INT IDENTITY PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (order_id) REFERENCES sales.orders(order_id),
    FOREIGN KEY (product_id) REFERENCES inventory.products(product_id)
)
GO

CREATE TABLE inventory.suppliers (
    supplier_id INT IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address VARCHAR(200),
    city VARCHAR(50),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
)
GO

-- Add foreign key after creating suppliers table
ALTER TABLE inventory.products
ADD CONSTRAINT fk_products_supplier
FOREIGN KEY (supplier_id) REFERENCES inventory.suppliers(supplier_id)
GO

CREATE TABLE inventory.inventory_transactions (
    transaction_id INT IDENTITY PRIMARY KEY,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    transaction_type VARCHAR(20) NOT NULL, -- 'in', 'out', 'adjustment'
    reference_id INT, -- order_id or purchase_id
    reference_type VARCHAR(20), -- 'order', 'purchase'
    notes TEXT,
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (product_id) REFERENCES inventory.products(product_id)
)
GO

CREATE TABLE hr.employees (
    employee_id INT IDENTITY PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    hire_date DATE NOT NULL,
    job_title VARCHAR(50),
    department VARCHAR(50),
    salary DECIMAL(10, 2),
    manager_id INT,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (manager_id) REFERENCES hr.employees(employee_id)
)
GO

-- Create views
CREATE VIEW sales.customer_orders AS
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    o.order_id,
    o.order_date,
    o.status,
    o.total_amount
FROM 
    sales.customers c
JOIN 
    sales.orders o ON c.customer_id = o.customer_id
GO

CREATE VIEW inventory.product_inventory AS
SELECT 
    p.product_id,
    p.name,
    p.sku,
    p.price,
    p.stock_quantity,
    s.name AS supplier_name,
    s.contact_name AS supplier_contact
FROM 
    inventory.products p
LEFT JOIN 
    inventory.suppliers s ON p.supplier_id = s.supplier_id
GO

CREATE VIEW sales.order_details AS
SELECT 
    o.order_id,
    o.order_date,
    o.status,
    c.customer_id,
    c.first_name + ' ' + c.last_name AS customer_name,
    oi.product_id,
    p.name AS product_name,
    oi.quantity,
    oi.unit_price,
    oi.subtotal
FROM 
    sales.orders o
JOIN 
    sales.customers c ON o.customer_id = c.customer_id
JOIN 
    sales.order_items oi ON o.order_id = oi.order_id
JOIN 
    inventory.products p ON oi.product_id = p.product_id
GO

-- Create stored procedures
CREATE PROCEDURE sales.create_order
    @customer_id INT,
    @shipping_address VARCHAR(200),
    @shipping_city VARCHAR(50),
    @shipping_state VARCHAR(50),
    @shipping_zip_code VARCHAR(20),
    @order_id INT OUTPUT
AS
BEGIN
    INSERT INTO sales.orders (
        customer_id,
        shipping_address,
        shipping_city,
        shipping_state,
        shipping_zip_code
    ) VALUES (
        @customer_id,
        @shipping_address,
        @shipping_city,
        @shipping_state,
        @shipping_zip_code
    )
    
    SET @order_id = SCOPE_IDENTITY()
    
    RETURN 0
END
GO

CREATE PROCEDURE sales.add_order_item
    @order_id INT,
    @product_id INT,
    @quantity INT
AS
BEGIN
    DECLARE @unit_price DECIMAL(10, 2)
    DECLARE @subtotal DECIMAL(10, 2)
    DECLARE @current_stock INT
    
    -- Get product price and check stock
    SELECT 
        @unit_price = price,
        @current_stock = stock_quantity
    FROM 
        inventory.products
    WHERE 
        product_id = @product_id
    
    IF @current_stock < @quantity
    BEGIN
        RAISERROR('Insufficient stock for product', 16, 1)
        RETURN 1
    END
    
    -- Calculate subtotal
    SET @subtotal = @unit_price * @quantity
    
    -- Add order item
    INSERT INTO sales.order_items (
        order_id,
        product_id,
        quantity,
        unit_price,
        subtotal
    ) VALUES (
        @order_id,
        @product_id,
        @quantity,
        @unit_price,
        @subtotal
    )
    
    -- Update order total
    UPDATE sales.orders
    SET total_amount = total_amount + @subtotal
    WHERE order_id = @order_id
    
    -- Update product stock
    UPDATE inventory.products
    SET stock_quantity = stock_quantity - @quantity
    WHERE product_id = @product_id
    
    -- Record inventory transaction
    INSERT INTO inventory.inventory_transactions (
        product_id,
        quantity,
        transaction_type,
        reference_id,
        reference_type,
        notes
    ) VALUES (
        @product_id,
        @quantity * -1,
        'out',
        @order_id,
        'order',
        'Order item added'
    )
    
    RETURN 0
END
GO

CREATE PROCEDURE inventory.update_product_stock
    @product_id INT,
    @quantity INT,
    @transaction_type VARCHAR(20),
    @reference_id INT = NULL,
    @reference_type VARCHAR(20) = NULL,
    @notes TEXT = NULL
AS
BEGIN
    -- Update product stock
    IF @transaction_type = 'in'
    BEGIN
        UPDATE inventory.products
        SET stock_quantity = stock_quantity + @quantity
        WHERE product_id = @product_id
    END
    ELSE IF @transaction_type = 'out'
    BEGIN
        DECLARE @current_stock INT
        
        SELECT @current_stock = stock_quantity
        FROM inventory.products
        WHERE product_id = @product_id
        
        IF @current_stock < @quantity
        BEGIN
            RAISERROR('Insufficient stock for product', 16, 1)
            RETURN 1
        END
        
        UPDATE inventory.products
        SET stock_quantity = stock_quantity - @quantity
        WHERE product_id = @product_id
    END
    ELSE IF @transaction_type = 'adjustment'
    BEGIN
        UPDATE inventory.products
        SET stock_quantity = @quantity
        WHERE product_id = @product_id
    END
    ELSE
    BEGIN
        RAISERROR('Invalid transaction type', 16, 1)
        RETURN 1
    END
    
    -- Record inventory transaction
    DECLARE @transaction_quantity INT
    
    IF @transaction_type = 'out'
        SET @transaction_quantity = @quantity * -1
    ELSE IF @transaction_type = 'in'
        SET @transaction_quantity = @quantity
    ELSE
        SET @transaction_quantity = @quantity
    
    INSERT INTO inventory.inventory_transactions (
        product_id,
        quantity,
        transaction_type,
        reference_id,
        reference_type,
        notes
    ) VALUES (
        @product_id,
        @transaction_quantity,
        @transaction_type,
        @reference_id,
        @reference_type,
        @notes
    )
    
    RETURN 0
END
GO

CREATE PROCEDURE hr.get_employee_hierarchy
    @employee_id INT
AS
BEGIN
    WITH EmployeeHierarchy AS (
        -- Base case: the employee we're looking for
        SELECT 
            employee_id,
            first_name,
            last_name,
            job_title,
            department,
            manager_id,
            0 AS level
        FROM 
            hr.employees
        WHERE 
            employee_id = @employee_id
        
        UNION ALL
        
        -- Recursive case: the managers above
        SELECT 
            e.employee_id,
            e.first_name,
            e.last_name,
            e.job_title,
            e.department,
            e.manager_id,
            eh.level + 1
        FROM 
            hr.employees e
        JOIN 
            EmployeeHierarchy eh ON e.employee_id = eh.manager_id
    )
    
    SELECT 
        employee_id,
        first_name,
        last_name,
        job_title,
        department,
        manager_id,
        level
    FROM 
        EmployeeHierarchy
    ORDER BY 
        level DESC
END
GO

-- Create functions
CREATE FUNCTION sales.calculate_order_total(
    @order_id INT
)
RETURNS DECIMAL(10, 2)
AS
BEGIN
    DECLARE @total DECIMAL(10, 2)
    
    SELECT @total = SUM(subtotal)
    FROM sales.order_items
    WHERE order_id = @order_id
    
    RETURN ISNULL(@total, 0)
END
GO

CREATE FUNCTION inventory.get_product_value(
    @product_id INT = NULL
)
RETURNS TABLE
AS
RETURN (
    SELECT 
        p.product_id,
        p.name,
        p.sku,
        p.stock_quantity,
        p.cost,
        p.stock_quantity * p.cost AS inventory_value
    FROM 
        inventory.products p
    WHERE 
        p.product_id = @product_id OR @product_id IS NULL
)
GO

-- Create triggers
CREATE TRIGGER sales.trg_update_order_total
ON sales.order_items
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get affected order IDs
    DECLARE @affected_orders TABLE (order_id INT)
    
    INSERT INTO @affected_orders
    SELECT order_id FROM inserted
    UNION
    SELECT order_id FROM deleted
    
    -- Update order totals
    UPDATE o
    SET 
        o.total_amount = sales.calculate_order_total(o.order_id),
        o.updated_at = GETDATE()
    FROM 
        sales.orders o
    JOIN 
        @affected_orders ao ON o.order_id = ao.order_id
END
GO

CREATE TRIGGER inventory.trg_update_product_timestamp
ON inventory.products
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    
    UPDATE p
    SET updated_at = GETDATE()
    FROM inventory.products p
    JOIN inserted i ON p.product_id = i.product_id
END
GO

-- Insert sample data
INSERT INTO inventory.suppliers (name, contact_name, email, phone)
VALUES 
    ('Acme Supplies', 'John Doe', 'john@acme.com', '555-1234'),
    ('XYZ Corporation', 'Jane Smith', 'jane@xyz.com', '555-5678'),
    ('Global Goods', 'Bob Johnson', 'bob@globalgoods.com', '555-9012')
GO

INSERT INTO inventory.products (name, description, sku, price, cost, stock_quantity, category, supplier_id)
VALUES 
    ('Laptop', 'High-performance laptop', 'LT-001', 1200.00, 900.00, 50, 'Electronics', 1),
    ('Smartphone', 'Latest smartphone model', 'SP-001', 800.00, 600.00, 100, 'Electronics', 1),
    ('Office Chair', 'Ergonomic office chair', 'OC-001', 250.00, 150.00, 30, 'Furniture', 2),
    ('Desk', 'Wooden desk', 'DK-001', 350.00, 200.00, 20, 'Furniture', 2),
    ('Printer', 'Color laser printer', 'PR-001', 400.00, 300.00, 15, 'Electronics', 3),
    ('Notebook', 'Spiral notebook', 'NB-001', 5.00, 2.00, 500, 'Office Supplies', 3)
GO

INSERT INTO hr.employees (first_name, last_name, email, phone, hire_date, job_title, department, salary)
VALUES 
    ('Michael', 'Scott', 'michael@company.com', '555-1111', '2010-01-15', 'Regional Manager', 'Management', 75000.00),
    ('Jim', 'Halpert', 'jim@company.com', '555-2222', '2012-03-20', 'Sales Representative', 'Sales', 50000.00),
    ('Pam', 'Beesly', 'pam@company.com', '555-3333', '2012-05-10', 'Receptionist', 'Administration', 45000.00),
    ('Dwight', 'Schrute', 'dwight@company.com', '555-4444', '2011-02-25', 'Assistant Regional Manager', 'Sales', 55000.00)
GO

-- Update manager IDs
UPDATE hr.employees
SET manager_id = 1
WHERE employee_id IN (2, 3, 4)
GO

INSERT INTO sales.customers (first_name, last_name, email, phone, address, city, state, zip_code)
VALUES 
    ('Alice', 'Johnson', 'alice@email.com', '555-1111', '123 Main St', 'New York', 'NY', '10001'),
    ('Bob', 'Smith', 'bob@email.com', '555-2222', '456 Oak Ave', 'Los Angeles', 'CA', '90001'),
    ('Charlie', 'Brown', 'charlie@email.com', '555-3333', '789 Pine Rd', 'Chicago', 'IL', '60601'),
    ('Diana', 'Miller', 'diana@email.com', '555-4444', '321 Elm St', 'Houston', 'TX', '77001')
GO

-- Create some orders
DECLARE @order_id INT

EXEC sales.create_order 1, '123 Main St', 'New York', 'NY', '10001', @order_id OUTPUT
EXEC sales.add_order_item @order_id, 1, 2
EXEC sales.add_order_item @order_id, 3, 1

EXEC sales.create_order 2, '456 Oak Ave', 'Los Angeles', 'CA', '90001', @order_id OUTPUT
EXEC sales.add_order_item @order_id, 2, 1
EXEC sales.add_order_item @order_id, 5, 1

EXEC sales.create_order 3, '789 Pine Rd', 'Chicago', 'IL', '60601', @order_id OUTPUT
EXEC sales.add_order_item @order_id, 4, 1
EXEC sales.add_order_item @order_id, 6, 5
GO

-- Print success message
PRINT 'Sample database created successfully!'
GO
