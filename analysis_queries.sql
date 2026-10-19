
USE sales_analytics;

-- 1. Overall KPIs: Total Sales, Cost, and Profit
SELECT
    SUM(Sales) AS total_sales,
    SUM(Cost) AS total_cost,
    SUM(Profit) AS total_profit
FROM sales_data;


-- 2. Regional Sales and Profit
SELECT
    Region,
    SUM(Sales) AS total_sales,
    SUM(Profit) AS total_profit
FROM sales_data
GROUP BY Region
ORDER BY total_sales DESC;


-- 3. Product-wise Sales and Profit
SELECT
    Product,
    SUM(Sales) AS total_sales,
    SUM(Profit) AS total_profit
FROM sales_data
GROUP BY Product
ORDER BY total_sales DESC;


-- 4. Monthly Sales and Profit Trends
SELECT
    Year,
    Month,
    SUM(Sales) AS monthly_sales,
    SUM(Profit) AS monthly_profit
FROM sales_data
GROUP BY Year, Month
ORDER BY Year, Month;
