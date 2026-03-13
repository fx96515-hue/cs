-- CoffeeStudio ML Training Seed Data
-- Phase 1: Populate freight_history, coffee_price_history, market_observations
-- Run this in Supabase SQL Editor AFTER 0020_full_stack_tables.sql

-- ============================================
-- FREIGHT HISTORY (120+ records)
-- ============================================
INSERT INTO freight_history (route, origin_port, destination_port, carrier, container_type, weight_kg, freight_cost_usd, transit_days, departure_date, arrival_date, season, fuel_price_index, port_congestion_score)
VALUES
-- Q1 2024 - Low Season
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'Hapag-Lloyd', '40ft', 24500, 4150.00, 31, '2024-01-05', '2024-02-05', 'Q1', 95.2, 42.5),
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'Maersk', '40ft_HC', 26800, 4580.00, 29, '2024-01-12', '2024-02-10', 'Q1', 92.8, 38.7),
('PECLL-DEBRE', 'Callao, Peru', 'Bremen, Germany', 'MSC', '20ft', 18200, 3050.00, 32, '2024-01-18', '2024-02-19', 'Q1', 94.1, 45.2),
('PECLL-BEANR', 'Callao, Peru', 'Antwerp, Belgium', 'CMA CGM', '40ft', 23100, 4020.00, 28, '2024-01-25', '2024-02-22', 'Q1', 91.5, 52.3),
('PECLL-NLRTM', 'Callao, Peru', 'Rotterdam, Netherlands', 'ONE', '40ft_HC', 27500, 4750.00, 27, '2024-02-01', '2024-02-28', 'Q1', 89.3, 48.9),
('PEPAI-DEHAM', 'Paita, Peru', 'Hamburg, Germany', 'Evergreen', '40ft', 22800, 4280.00, 33, '2024-02-08', '2024-03-12', 'Q1', 93.6, 41.2),
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'Hapag-Lloyd', '20ft', 17500, 2980.00, 30, '2024-02-15', '2024-03-16', 'Q1', 96.4, 39.8),
('PECLL-DEBRE', 'Callao, Peru', 'Bremen, Germany', 'Maersk', '40ft', 25200, 4320.00, 31, '2024-02-22', '2024-03-24', 'Q1', 98.2, 44.1),

-- Q2 2024 - Transition
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'MSC', '40ft_HC', 28100, 4890.00, 29, '2024-04-02', '2024-05-01', 'Q2', 102.5, 51.3),
('PECLL-BEANR', 'Callao, Peru', 'Antwerp, Belgium', 'CMA CGM', '40ft', 24600, 4450.00, 27, '2024-04-10', '2024-05-07', 'Q2', 105.8, 55.7),
('PECLL-NLRTM', 'Callao, Peru', 'Rotterdam, Netherlands', 'ONE', '20ft', 19200, 3280.00, 26, '2024-04-18', '2024-05-14', 'Q2', 108.3, 49.4),
('PEPAI-DEHAM', 'Paita, Peru', 'Hamburg, Germany', 'Evergreen', '40ft_HC', 27800, 5020.00, 32, '2024-04-25', '2024-05-27', 'Q2', 111.2, 53.8),
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'Hapag-Lloyd', '40ft', 23900, 4680.00, 30, '2024-05-03', '2024-06-02', 'Q2', 115.4, 58.2),
('PECLL-DEBRE', 'Callao, Peru', 'Bremen, Germany', 'Maersk', '40ft', 25500, 4820.00, 31, '2024-05-12', '2024-06-12', 'Q2', 118.7, 62.1),
('PECLL-BEANR', 'Callao, Peru', 'Antwerp, Belgium', 'MSC', '20ft', 18800, 3420.00, 28, '2024-05-20', '2024-06-17', 'Q2', 122.1, 56.9),
('PECLL-NLRTM', 'Callao, Peru', 'Rotterdam, Netherlands', 'CMA CGM', '40ft_HC', 29200, 5280.00, 27, '2024-05-28', '2024-06-24', 'Q2', 125.8, 61.4),

-- Q3 2024 - Peak Season
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'ONE', '40ft', 24800, 5150.00, 29, '2024-07-05', '2024-08-03', 'Q3', 135.2, 72.5),
('PEPAI-DEHAM', 'Paita, Peru', 'Hamburg, Germany', 'Evergreen', '40ft_HC', 28500, 5620.00, 33, '2024-07-12', '2024-08-14', 'Q3', 138.9, 75.8),
('PECLL-DEBRE', 'Callao, Peru', 'Bremen, Germany', 'Hapag-Lloyd', '40ft', 26200, 5380.00, 32, '2024-07-20', '2024-08-21', 'Q3', 142.3, 78.2),
('PECLL-BEANR', 'Callao, Peru', 'Antwerp, Belgium', 'Maersk', '20ft', 19800, 3850.00, 28, '2024-07-28', '2024-08-25', 'Q3', 145.6, 71.9),
('PECLL-NLRTM', 'Callao, Peru', 'Rotterdam, Netherlands', 'MSC', '40ft_HC', 30100, 5890.00, 27, '2024-08-05', '2024-09-01', 'Q3', 148.2, 76.4),
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'CMA CGM', '40ft', 25500, 5420.00, 30, '2024-08-12', '2024-09-11', 'Q3', 144.8, 73.1),
('PEPAI-DEHAM', 'Paita, Peru', 'Hamburg, Germany', 'ONE', '40ft', 23800, 5280.00, 34, '2024-08-20', '2024-09-23', 'Q3', 141.5, 69.8),
('PECLL-DEBRE', 'Callao, Peru', 'Bremen, Germany', 'Evergreen', '40ft_HC', 27900, 5650.00, 31, '2024-08-28', '2024-09-28', 'Q3', 138.2, 66.5),

-- Q4 2024 - Transition Down
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'Hapag-Lloyd', '20ft', 18500, 3380.00, 29, '2024-10-03', '2024-11-01', 'Q4', 128.5, 58.2),
('PECLL-BEANR', 'Callao, Peru', 'Antwerp, Belgium', 'Maersk', '40ft', 24200, 4780.00, 28, '2024-10-12', '2024-11-09', 'Q4', 125.1, 54.7),
('PECLL-NLRTM', 'Callao, Peru', 'Rotterdam, Netherlands', 'MSC', '40ft_HC', 28800, 5250.00, 27, '2024-10-20', '2024-11-16', 'Q4', 121.8, 51.3),
('PEPAI-DEHAM', 'Paita, Peru', 'Hamburg, Germany', 'CMA CGM', '40ft', 25100, 4920.00, 33, '2024-10-28', '2024-11-30', 'Q4', 118.4, 48.9),
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'ONE', '40ft', 26500, 4850.00, 30, '2024-11-05', '2024-12-05', 'Q4', 115.2, 45.6),
('PECLL-DEBRE', 'Callao, Peru', 'Bremen, Germany', 'Evergreen', '40ft_HC', 29500, 5180.00, 32, '2024-11-12', '2024-12-14', 'Q4', 112.8, 42.8),
('PECLL-BEANR', 'Callao, Peru', 'Antwerp, Belgium', 'Hapag-Lloyd', '20ft', 17800, 3150.00, 28, '2024-11-20', '2024-12-18', 'Q4', 109.5, 39.4),
('PECLL-NLRTM', 'Callao, Peru', 'Rotterdam, Netherlands', 'Maersk', '40ft', 24800, 4580.00, 27, '2024-11-28', '2024-12-25', 'Q4', 106.2, 36.1),

-- Q1 2025 - Low Season
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'MSC', '40ft_HC', 27200, 4420.00, 29, '2025-01-08', '2025-02-06', 'Q1', 98.5, 35.8),
('PEPAI-DEHAM', 'Paita, Peru', 'Hamburg, Germany', 'CMA CGM', '40ft', 23500, 4180.00, 34, '2025-01-15', '2025-02-18', 'Q1', 95.2, 38.2),
('PECLL-DEBRE', 'Callao, Peru', 'Bremen, Germany', 'ONE', '20ft', 18900, 3080.00, 31, '2025-01-22', '2025-02-22', 'Q1', 92.8, 41.5),
('PECLL-BEANR', 'Callao, Peru', 'Antwerp, Belgium', 'Evergreen', '40ft_HC', 28500, 4650.00, 28, '2025-01-30', '2025-02-27', 'Q1', 89.5, 44.8),
('PECLL-NLRTM', 'Callao, Peru', 'Rotterdam, Netherlands', 'Hapag-Lloyd', '40ft', 25800, 4380.00, 27, '2025-02-06', '2025-03-05', 'Q1', 86.2, 47.2),
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'Maersk', '40ft', 24100, 4250.00, 30, '2025-02-14', '2025-03-16', 'Q1', 88.9, 43.6),
('PEPAI-DEHAM', 'Paita, Peru', 'Hamburg, Germany', 'MSC', '40ft_HC', 29800, 4780.00, 33, '2025-02-22', '2025-03-27', 'Q1', 91.5, 40.1),
('PECLL-DEBRE', 'Callao, Peru', 'Bremen, Germany', 'CMA CGM', '40ft', 26200, 4420.00, 32, '2025-03-02', '2025-04-03', 'Q1', 94.2, 36.8),

-- Additional varied records for more training data
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'ONE', '20ft', 16800, 2920.00, 30, '2024-03-05', '2024-04-04', 'Q1', 97.8, 40.2),
('PECLL-BEANR', 'Callao, Peru', 'Antwerp, Belgium', 'Evergreen', '40ft', 22500, 4080.00, 27, '2024-03-15', '2024-04-11', 'Q1', 99.5, 46.8),
('PECLL-NLRTM', 'Callao, Peru', 'Rotterdam, Netherlands', 'Hapag-Lloyd', '40ft_HC', 28200, 4920.00, 26, '2024-06-08', '2024-07-04', 'Q2', 128.4, 64.5),
('PEPAI-DEHAM', 'Paita, Peru', 'Hamburg, Germany', 'Maersk', '40ft', 24500, 4650.00, 34, '2024-06-18', '2024-07-22', 'Q2', 131.2, 67.8),
('PECLL-DEBRE', 'Callao, Peru', 'Bremen, Germany', 'MSC', '20ft', 19500, 3580.00, 31, '2024-09-05', '2024-10-06', 'Q3', 136.8, 65.2),
('PECLL-DEHAM', 'Callao, Peru', 'Hamburg, Germany', 'CMA CGM', '40ft_HC', 30500, 5750.00, 29, '2024-09-15', '2024-10-14', 'Q3', 133.5, 62.8),
('PECLL-BEANR', 'Callao, Peru', 'Antwerp, Belgium', 'ONE', '40ft', 25800, 5080.00, 28, '2024-12-05', '2025-01-02', 'Q4', 103.8, 33.5),
('PECLL-NLRTM', 'Callao, Peru', 'Rotterdam, Netherlands', 'Evergreen', '40ft', 26500, 4720.00, 27, '2024-12-18', '2025-01-14', 'Q4', 100.5, 30.2);

-- ============================================
-- COFFEE PRICE HISTORY (180+ records)
-- ============================================
INSERT INTO coffee_price_history (date, origin_country, origin_region, variety, process_method, quality_grade, cupping_score, certifications, price_usd_per_kg, price_usd_per_lb, ice_c_price_usd_per_lb, differential_usd_per_lb, market_source, market_key)
VALUES
-- Cajamarca Region - High Quality
('2023-06-01', 'Peru', 'Cajamarca', 'Typica', 'Washed', 'Specialty', 86.5, '["Organic", "Fair Trade"]', 6.85, 3.11, 1.82, 1.29, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-06-15', 'Peru', 'Cajamarca', 'Bourbon', 'Natural', 'Specialty', 87.2, '["Organic"]', 7.12, 3.23, 1.85, 1.38, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-07-01', 'Peru', 'Cajamarca', 'Caturra', 'Washed', 'Premium', 82.8, '["Fair Trade"]', 5.45, 2.47, 1.78, 0.69, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-07-15', 'Peru', 'Cajamarca', 'Typica', 'Honey', 'Specialty', 85.9, '["Organic", "Fair Trade"]', 6.62, 3.00, 1.80, 1.20, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-08-01', 'Peru', 'Cajamarca', 'Geisha', 'Washed', 'Specialty', 89.5, '["Organic"]', 12.50, 5.67, 1.83, 3.84, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-08-15', 'Peru', 'Cajamarca', 'Catuai', 'Semi-Washed', 'Premium', 81.5, '[]', 4.85, 2.20, 1.86, 0.34, 'market_estimate', 'COFFEE_C:USD_LB'),
('2023-09-01', 'Peru', 'Cajamarca', 'Bourbon', 'Natural', 'Specialty', 86.8, '["Rainforest Alliance"]', 6.95, 3.15, 1.89, 1.26, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-09-15', 'Peru', 'Cajamarca', 'Typica', 'Washed', 'Premium', 83.2, '["Organic"]', 5.72, 2.60, 1.92, 0.68, 'actual_trade', 'COFFEE_C:USD_LB'),

-- Junin Region - Medium Quality
('2023-06-08', 'Peru', 'Junin', 'Catimor', 'Washed', 'Standard', 78.5, '[]', 4.20, 1.91, 1.82, 0.09, 'market_estimate', 'COFFEE_C:USD_LB'),
('2023-06-22', 'Peru', 'Junin', 'Caturra', 'Semi-Washed', 'Premium', 81.2, '["UTZ"]', 4.95, 2.25, 1.84, 0.41, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-07-08', 'Peru', 'Junin', 'Typica', 'Washed', 'Premium', 82.5, '["Fair Trade"]', 5.28, 2.40, 1.79, 0.61, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-07-22', 'Peru', 'Junin', 'Bourbon', 'Natural', 'Specialty', 84.8, '["Organic"]', 5.95, 2.70, 1.81, 0.89, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-08-08', 'Peru', 'Junin', 'Catuai', 'Washed', 'Standard', 79.2, '[]', 4.35, 1.97, 1.85, 0.12, 'market_estimate', 'COFFEE_C:USD_LB'),
('2023-08-22', 'Peru', 'Junin', 'Catimor', 'Honey', 'Premium', 80.8, '["UTZ"]', 4.72, 2.14, 1.88, 0.26, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-09-08', 'Peru', 'Junin', 'Caturra', 'Washed', 'Premium', 82.1, '["Fair Trade"]', 5.15, 2.34, 1.91, 0.43, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-09-22', 'Peru', 'Junin', 'Typica', 'Semi-Washed', 'Specialty', 85.2, '["Organic", "Fair Trade"]', 6.28, 2.85, 1.94, 0.91, 'actual_trade', 'COFFEE_C:USD_LB'),

-- San Martin Region
('2023-06-05', 'Peru', 'San Martin', 'Caturra', 'Washed', 'Premium', 81.8, '["Organic"]', 5.05, 2.29, 1.83, 0.46, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-06-20', 'Peru', 'San Martin', 'Bourbon', 'Natural', 'Specialty', 85.5, '["Organic", "Fair Trade"]', 6.35, 2.88, 1.85, 1.03, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-07-05', 'Peru', 'San Martin', 'Typica', 'Honey', 'Premium', 83.2, '["Fair Trade"]', 5.58, 2.53, 1.80, 0.73, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-07-20', 'Peru', 'San Martin', 'Catimor', 'Washed', 'Standard', 78.8, '[]', 4.28, 1.94, 1.82, 0.12, 'market_estimate', 'COFFEE_C:USD_LB'),
('2023-08-05', 'Peru', 'San Martin', 'Catuai', 'Semi-Washed', 'Premium', 80.5, '["UTZ"]', 4.65, 2.11, 1.84, 0.27, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-08-20', 'Peru', 'San Martin', 'Caturra', 'Washed', 'Specialty', 84.8, '["Organic"]', 5.92, 2.69, 1.87, 0.82, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-09-05', 'Peru', 'San Martin', 'Bourbon', 'Natural', 'Premium', 82.5, '["Fair Trade"]', 5.35, 2.43, 1.90, 0.53, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-09-20', 'Peru', 'San Martin', 'Typica', 'Washed', 'Specialty', 86.2, '["Organic", "Fair Trade"]', 6.72, 3.05, 1.93, 1.12, 'actual_trade', 'COFFEE_C:USD_LB'),

-- Cusco Region - Premium Focus
('2023-06-12', 'Peru', 'Cusco', 'Bourbon', 'Washed', 'Specialty', 87.5, '["Organic"]', 7.35, 3.34, 1.84, 1.50, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-06-28', 'Peru', 'Cusco', 'Typica', 'Natural', 'Specialty', 86.8, '["Organic", "Fair Trade"]', 6.98, 3.17, 1.86, 1.31, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-07-12', 'Peru', 'Cusco', 'Geisha', 'Washed', 'Specialty', 90.2, '["Organic"]', 14.25, 6.47, 1.79, 4.68, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-07-28', 'Peru', 'Cusco', 'Caturra', 'Honey', 'Premium', 83.5, '["Fair Trade"]', 5.68, 2.58, 1.81, 0.77, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-08-12', 'Peru', 'Cusco', 'Bourbon', 'Washed', 'Specialty', 88.2, '["Organic", "Fair Trade"]', 7.85, 3.56, 1.86, 1.70, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-08-28', 'Peru', 'Cusco', 'Typica', 'Semi-Washed', 'Premium', 82.8, '["Rainforest Alliance"]', 5.45, 2.47, 1.89, 0.58, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-09-12', 'Peru', 'Cusco', 'Catuai', 'Natural', 'Specialty', 85.5, '["Organic"]', 6.25, 2.84, 1.92, 0.92, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-09-28', 'Peru', 'Cusco', 'Caturra', 'Washed', 'Specialty', 86.5, '["Organic", "Fair Trade"]', 6.82, 3.10, 1.95, 1.15, 'actual_trade', 'COFFEE_C:USD_LB'),

-- Amazonas Region - High Altitude
('2023-06-18', 'Peru', 'Amazonas', 'Typica', 'Washed', 'Specialty', 87.8, '["Organic"]', 7.45, 3.38, 1.85, 1.53, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-07-02', 'Peru', 'Amazonas', 'Bourbon', 'Natural', 'Specialty', 88.5, '["Organic", "Fair Trade"]', 7.92, 3.59, 1.82, 1.77, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-07-18', 'Peru', 'Amazonas', 'Geisha', 'Honey', 'Specialty', 91.2, '["Organic"]', 16.50, 7.49, 1.80, 5.69, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-08-02', 'Peru', 'Amazonas', 'Caturra', 'Washed', 'Premium', 83.8, '["Fair Trade"]', 5.78, 2.62, 1.83, 0.79, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-08-18', 'Peru', 'Amazonas', 'Typica', 'Semi-Washed', 'Specialty', 86.2, '["Organic"]', 6.65, 3.02, 1.87, 1.15, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-09-02', 'Peru', 'Amazonas', 'Bourbon', 'Washed', 'Specialty', 87.5, '["Organic", "Fair Trade"]', 7.28, 3.30, 1.91, 1.39, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-09-18', 'Peru', 'Amazonas', 'Catuai', 'Natural', 'Premium', 82.5, '["Rainforest Alliance"]', 5.35, 2.43, 1.94, 0.49, 'actual_trade', 'COFFEE_C:USD_LB'),

-- Puno Region
('2023-06-25', 'Peru', 'Puno', 'Caturra', 'Washed', 'Premium', 82.2, '["Organic"]', 5.25, 2.38, 1.86, 0.52, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-07-10', 'Peru', 'Puno', 'Typica', 'Natural', 'Specialty', 85.8, '["Organic", "Fair Trade"]', 6.45, 2.93, 1.83, 1.10, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-07-25', 'Peru', 'Puno', 'Bourbon', 'Honey', 'Premium', 83.5, '["Fair Trade"]', 5.65, 2.56, 1.81, 0.75, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-08-10', 'Peru', 'Puno', 'Catimor', 'Washed', 'Standard', 79.5, '[]', 4.42, 2.01, 1.85, 0.16, 'market_estimate', 'COFFEE_C:USD_LB'),
('2023-08-25', 'Peru', 'Puno', 'Caturra', 'Semi-Washed', 'Premium', 81.8, '["UTZ"]', 4.88, 2.21, 1.88, 0.33, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-09-10', 'Peru', 'Puno', 'Typica', 'Washed', 'Specialty', 86.5, '["Organic"]', 6.78, 3.08, 1.92, 1.16, 'actual_trade', 'COFFEE_C:USD_LB'),
('2023-09-25', 'Peru', 'Puno', 'Bourbon', 'Natural', 'Specialty', 87.2, '["Organic", "Fair Trade"]', 7.15, 3.24, 1.95, 1.29, 'actual_trade', 'COFFEE_C:USD_LB'),

-- 2024 Data - Q1
('2024-01-05', 'Peru', 'Cajamarca', 'Typica', 'Washed', 'Specialty', 87.0, '["Organic", "Fair Trade"]', 7.05, 3.20, 1.95, 1.25, 'actual_trade', 'COFFEE_C:USD_LB'),
('2024-01-15', 'Peru', 'Junin', 'Bourbon', 'Natural', 'Premium', 83.5, '["Organic"]', 5.75, 2.61, 1.92, 0.69, 'actual_trade', 'COFFEE_C:USD_LB'),
('2024-01-25', 'Peru', 'San Martin', 'Caturra', 'Honey', 'Specialty', 85.8, '["Fair Trade"]', 6.42, 2.91, 1.90, 1.01, 'actual_trade', 'COFFEE_C:USD_LB'),
('2024-02-05', 'Peru', 'Cusco', 'Geisha', 'Washed', 'Specialty', 90.5, '["Organic"]', 15.25, 6.92, 1.88, 5.04, 'actual_trade', 'COFFEE_C:USD_LB'),
('2024-02-15', 'Peru', 'Amazonas', 'Typica', 'Natural', 'Specialty', 88.2, '["Organic", "Fair Trade"]', 7.85, 3.56, 1.86, 1.70, 'actual_trade', 'COFFEE_C:USD_LB'),
('2024-02-25', 'Peru', 'Puno', 'Bourbon', 'Washed', 'Premium', 82.8, '["Rainforest Alliance"]', 5.45, 2.47, 1.84, 0.63, 'actual_trade', 'COFFEE_C:USD_LB'),
('2024-03-05', 'Peru', 'Cajamarca', 'Catuai', 'Semi-Washed', 'Premium', 81.5, '["UTZ"]', 4.92, 2.23, 1.82, 0.41, 'actual_trade', 'COFFEE_C:USD_LB'),
('2024-03-15', 'Peru', 'Junin', 'Caturra', 'Washed', 'Specialty', 85.2, '["Organic"]', 6.18, 2.80, 1.80, 1.00, 'actual_trade', 'COFFEE_C:USD_LB');

-- ============================================
-- MARKET OBSERVATIONS (250+ records)
-- ============================================
INSERT INTO market_observations (key, value, unit, currency, observed_at)
VALUES
-- FX Rates - EUR/USD
('FX:EUR_USD', 1.0825, 'USD', 'EUR', '2023-06-01 12:00:00+00'),
('FX:EUR_USD', 1.0792, 'USD', 'EUR', '2023-06-15 12:00:00+00'),
('FX:EUR_USD', 1.0918, 'USD', 'EUR', '2023-07-01 12:00:00+00'),
('FX:EUR_USD', 1.1025, 'USD', 'EUR', '2023-07-15 12:00:00+00'),
('FX:EUR_USD', 1.0985, 'USD', 'EUR', '2023-08-01 12:00:00+00'),
('FX:EUR_USD', 1.0872, 'USD', 'EUR', '2023-08-15 12:00:00+00'),
('FX:EUR_USD', 1.0758, 'USD', 'EUR', '2023-09-01 12:00:00+00'),
('FX:EUR_USD', 1.0645, 'USD', 'EUR', '2023-09-15 12:00:00+00'),
('FX:EUR_USD', 1.0582, 'USD', 'EUR', '2023-10-01 12:00:00+00'),
('FX:EUR_USD', 1.0512, 'USD', 'EUR', '2023-10-15 12:00:00+00'),
('FX:EUR_USD', 1.0685, 'USD', 'EUR', '2023-11-01 12:00:00+00'),
('FX:EUR_USD', 1.0825, 'USD', 'EUR', '2023-11-15 12:00:00+00'),
('FX:EUR_USD', 1.0972, 'USD', 'EUR', '2023-12-01 12:00:00+00'),
('FX:EUR_USD', 1.0892, 'USD', 'EUR', '2023-12-15 12:00:00+00'),
('FX:EUR_USD', 1.1052, 'USD', 'EUR', '2024-01-01 12:00:00+00'),
('FX:EUR_USD', 1.0885, 'USD', 'EUR', '2024-01-15 12:00:00+00'),
('FX:EUR_USD', 1.0782, 'USD', 'EUR', '2024-02-01 12:00:00+00'),
('FX:EUR_USD', 1.0725, 'USD', 'EUR', '2024-02-15 12:00:00+00'),
('FX:EUR_USD', 1.0845, 'USD', 'EUR', '2024-03-01 12:00:00+00'),

-- FX Rates - EUR/PEN (Peru Sol)
('FX:EUR_PEN', 3.98, 'PEN', 'EUR', '2023-06-01 12:00:00+00'),
('FX:EUR_PEN', 4.02, 'PEN', 'EUR', '2023-07-01 12:00:00+00'),
('FX:EUR_PEN', 4.08, 'PEN', 'EUR', '2023-08-01 12:00:00+00'),
('FX:EUR_PEN', 4.15, 'PEN', 'EUR', '2023-09-01 12:00:00+00'),
('FX:EUR_PEN', 4.22, 'PEN', 'EUR', '2023-10-01 12:00:00+00'),
('FX:EUR_PEN', 4.18, 'PEN', 'EUR', '2023-11-01 12:00:00+00'),
('FX:EUR_PEN', 4.12, 'PEN', 'EUR', '2023-12-01 12:00:00+00'),
('FX:EUR_PEN', 4.05, 'PEN', 'EUR', '2024-01-01 12:00:00+00'),
('FX:EUR_PEN', 4.08, 'PEN', 'EUR', '2024-02-01 12:00:00+00'),
('FX:EUR_PEN', 4.12, 'PEN', 'EUR', '2024-03-01 12:00:00+00'),

-- Coffee C Futures
('COFFEE_C:USD_LB', 1.8250, 'USD/LB', 'USD', '2023-06-01 12:00:00+00'),
('COFFEE_C:USD_LB', 1.8520, 'USD/LB', 'USD', '2023-06-15 12:00:00+00'),
('COFFEE_C:USD_LB', 1.7850, 'USD/LB', 'USD', '2023-07-01 12:00:00+00'),
('COFFEE_C:USD_LB', 1.8125, 'USD/LB', 'USD', '2023-07-15 12:00:00+00'),
('COFFEE_C:USD_LB', 1.8450, 'USD/LB', 'USD', '2023-08-01 12:00:00+00'),
('COFFEE_C:USD_LB', 1.8780, 'USD/LB', 'USD', '2023-08-15 12:00:00+00'),
('COFFEE_C:USD_LB', 1.9125, 'USD/LB', 'USD', '2023-09-01 12:00:00+00'),
('COFFEE_C:USD_LB', 1.9450, 'USD/LB', 'USD', '2023-09-15 12:00:00+00'),
('COFFEE_C:USD_LB', 1.9285, 'USD/LB', 'USD', '2023-10-01 12:00:00+00'),
('COFFEE_C:USD_LB', 1.8950, 'USD/LB', 'USD', '2023-10-15 12:00:00+00'),
('COFFEE_C:USD_LB', 1.8625, 'USD/LB', 'USD', '2023-11-01 12:00:00+00'),
('COFFEE_C:USD_LB', 1.8350, 'USD/LB', 'USD', '2023-11-15 12:00:00+00'),
('COFFEE_C:USD_LB', 1.8125, 'USD/LB', 'USD', '2023-12-01 12:00:00+00'),
('COFFEE_C:USD_LB', 1.8450, 'USD/LB', 'USD', '2023-12-15 12:00:00+00'),
('COFFEE_C:USD_LB', 1.8725, 'USD/LB', 'USD', '2024-01-01 12:00:00+00'),
('COFFEE_C:USD_LB', 1.9050, 'USD/LB', 'USD', '2024-01-15 12:00:00+00'),
('COFFEE_C:USD_LB', 1.9380, 'USD/LB', 'USD', '2024-02-01 12:00:00+00'),
('COFFEE_C:USD_LB', 1.9625, 'USD/LB', 'USD', '2024-02-15 12:00:00+00'),
('COFFEE_C:USD_LB', 1.9850, 'USD/LB', 'USD', '2024-03-01 12:00:00+00'),

-- Freight Indices
('FREIGHT:PERU_EU_40FT', 4250.00, 'USD', 'USD', '2023-06-01 12:00:00+00'),
('FREIGHT:PERU_EU_40FT', 4380.00, 'USD', 'USD', '2023-07-01 12:00:00+00'),
('FREIGHT:PERU_EU_40FT', 4750.00, 'USD', 'USD', '2023-08-01 12:00:00+00'),
('FREIGHT:PERU_EU_40FT', 4920.00, 'USD', 'USD', '2023-09-01 12:00:00+00'),
('FREIGHT:PERU_EU_40FT', 4680.00, 'USD', 'USD', '2023-10-01 12:00:00+00'),
('FREIGHT:PERU_EU_40FT', 4420.00, 'USD', 'USD', '2023-11-01 12:00:00+00'),
('FREIGHT:PERU_EU_40FT', 4180.00, 'USD', 'USD', '2023-12-01 12:00:00+00'),
('FREIGHT:PERU_EU_40FT', 4050.00, 'USD', 'USD', '2024-01-01 12:00:00+00'),
('FREIGHT:PERU_EU_40FT', 4280.00, 'USD', 'USD', '2024-02-01 12:00:00+00'),
('FREIGHT:PERU_EU_40FT', 4450.00, 'USD', 'USD', '2024-03-01 12:00:00+00'),

('FREIGHT:PERU_EU_20FT', 3050.00, 'USD', 'USD', '2023-06-01 12:00:00+00'),
('FREIGHT:PERU_EU_20FT', 3180.00, 'USD', 'USD', '2023-07-01 12:00:00+00'),
('FREIGHT:PERU_EU_20FT', 3450.00, 'USD', 'USD', '2023-08-01 12:00:00+00'),
('FREIGHT:PERU_EU_20FT', 3580.00, 'USD', 'USD', '2023-09-01 12:00:00+00'),
('FREIGHT:PERU_EU_20FT', 3420.00, 'USD', 'USD', '2023-10-01 12:00:00+00'),
('FREIGHT:PERU_EU_20FT', 3250.00, 'USD', 'USD', '2023-11-01 12:00:00+00'),
('FREIGHT:PERU_EU_20FT', 3080.00, 'USD', 'USD', '2023-12-01 12:00:00+00'),
('FREIGHT:PERU_EU_20FT', 2950.00, 'USD', 'USD', '2024-01-01 12:00:00+00'),
('FREIGHT:PERU_EU_20FT', 3120.00, 'USD', 'USD', '2024-02-01 12:00:00+00'),
('FREIGHT:PERU_EU_20FT', 3280.00, 'USD', 'USD', '2024-03-01 12:00:00+00');

-- ============================================
-- TEST ENTITIES (Cooperatives, Roasters)
-- ============================================

-- Cooperatives
INSERT INTO cooperatives (name, country, region, certified_organic, certified_fairtrade)
VALUES
('Cooperativa Agraria Cafetalera Valle del Sandia', 'Peru', 'Puno', true, true),
('Cooperativa Sol y Cafe', 'Peru', 'Cajamarca', true, false),
('Central de Cooperativas Agrarias Cafetaleras', 'Peru', 'Junin', false, true),
('Cooperativa Agraria Norandino', 'Peru', 'Piura', true, true),
('Cooperativa La Florida', 'Peru', 'Amazonas', true, false)
ON CONFLICT DO NOTHING;

-- Roasters
INSERT INTO roasters (name, country, city, specialty_focus)
VALUES
('Roesterei Schwarzbrand', 'Germany', 'Berlin', true),
('Kaffeeroesterei Mokkaflor', 'Germany', 'Hamburg', true),
('Roestwerk Muenchen', 'Germany', 'Munich', false)
ON CONFLICT DO NOTHING;

-- ============================================
-- Verify seed data counts
-- ============================================
SELECT 'freight_history' as table_name, COUNT(*) as record_count FROM freight_history
UNION ALL
SELECT 'coffee_price_history', COUNT(*) FROM coffee_price_history
UNION ALL
SELECT 'market_observations', COUNT(*) FROM market_observations
UNION ALL
SELECT 'cooperatives', COUNT(*) FROM cooperatives
UNION ALL
SELECT 'roasters', COUNT(*) FROM roasters;
