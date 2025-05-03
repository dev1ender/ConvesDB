questions = [
    {
        "question": "How many active customers are there in the database?",
        "sql": "SELECT COUNT(*) FROM customers WHERE status = 'active';",
        "expected_result": "41",
        "actual_result": "41"
    },
    {
        "question": "List the names and emails of all employees in the Technology department.",
        "sql": "SELECT first_name, last_name, email FROM employees WHERE department = 'Technology';",
        "expected_result": "first_name,last_name,email\nDavid,Chen,david.chen@example.com\nMichael,Brown,michael.brown@example.com\nLisa,Wang,lisa.wang@example.com\nRyan,Garcia,ryan.garcia@example.com\nTechFirst12,TechLast12,tech.employee12@example.com\nTechFirst13,TechLast13,tech.employee13@example.com\nTechFirst14,TechLast14,tech.employee14@example.com\nTechFirst17,TechLast17,tech.employee17@example.com\nTechFirst18,TechLast18,tech.employee18@example.com\nTechFirst19,TechLast19,tech.employee19@example.com\nTechFirst22,TechLast22,tech.employee22@example.com\nTechFirst23,TechLast23,tech.employee23@example.com\nTechFirst24,TechLast24,tech.employee24@example.com\nTechFirst27,TechLast27,tech.employee27@example.com\nTechFirst28,TechLast28,tech.employee28@example.com\nTechFirst29,TechLast29,tech.employee29@example.com\nTechFirst32,TechLast32,tech.employee32@example.com\nTechFirst33,TechLast33,tech.employee33@example.com\nTechFirst34,TechLast34,tech.employee34@example.com",
        "actual_result": "first_name,last_name,email\nDavid,Chen,david.chen@example.com\nMichael,Brown,michael.brown@example.com\nLisa,Wang,lisa.wang@example.com\nRyan,Garcia,ryan.garcia@example.com\nTechFirst12,TechLast12,tech.employee12@example.com\nTechFirst13,TechLast13,tech.employee13@example.com\nTechFirst14,TechLast14,tech.employee14@example.com\nTechFirst17,TechLast17,tech.employee17@example.com\nTechFirst18,TechLast18,tech.employee18@example.com\nTechFirst19,TechLast19,tech.employee19@example.com\nTechFirst22,TechLast22,tech.employee22@example.com\nTechFirst23,TechLast23,tech.employee23@example.com\nTechFirst24,TechLast24,tech.employee24@example.com\nTechFirst27,TechLast27,tech.employee27@example.com\nTechFirst28,TechLast28,tech.employee28@example.com\nTechFirst29,TechLast29,tech.employee29@example.com\nTechFirst32,TechLast32,tech.employee32@example.com\nTechFirst33,TechLast33,tech.employee33@example.com\nTechFirst34,TechLast34,tech.employee34@example.com"
    },
    {
        "question": "What is the total revenue from all delivered orders?",
        "sql": "SELECT SUM(total_amount) FROM orders WHERE status = 'delivered';",
        "expected_result": "163102.29",
        "actual_result": "163102.29"
    },
    {
        "question": "Which products have less than 10 units available in any inventory location?",
        "sql": "SELECT DISTINCT p.product_id, p.name FROM products p JOIN inventory i ON p.product_id = i.product_id WHERE i.quantity < 10;",
        "expected_result": "product_id,name\n26,Product 26\n52,Product 52\n12,Wireless Bluetooth Speaker\n73,Product 73\n42,Product 42\n95,Product 95\n90,Product 90\n2,Wireless Noise-Cancelling Headphones\n76,Product 76\n29,Product 29\n35,Product 35\n84,Product 84\n79,Product 79\n51,Product 51\n43,Product 43\n53,Product 53\n33,Product 33\n38,Product 38\n50,Product 50\n100,Product 100\n67,Product 67\n1,Ultra HD Smart TV 55\"\n39,Product 39\n15,Smart Robot Vacuum\n92,Product 92\n57,Product 57\n80,Product 80\n7,Professional Stand Mixer\n68,Product 68\n31,Product 31\n24,Product 24\n17,Product 17\n5,Smart Home Security System\n48,Product 48\n89,Product 89\n21,Product 21\n58,Product 58\n55,Product 55\n11,Yoga Mat Premium\n93,Product 93\n85,Product 85\n96,Product 96\n77,Product 77\n64,Product 64\n99,Product 99\n87,Product 87\n27,Product 27",
        "actual_result": "product_id,name\n26,Product 26\n52,Product 52\n12,Wireless Bluetooth Speaker\n73,Product 73\n42,Product 42\n95,Product 95\n90,Product 90\n2,Wireless Noise-Cancelling Headphones\n76,Product 76\n29,Product 29\n35,Product 35\n84,Product 84\n79,Product 79\n51,Product 51\n43,Product 43\n53,Product 53\n33,Product 33\n38,Product 38\n50,Product 50\n100,Product 100\n67,Product 67\n1,Ultra HD Smart TV 55\"\n39,Product 39\n15,Smart Robot Vacuum\n92,Product 92\n57,Product 57\n80,Product 80\n7,Professional Stand Mixer\n68,Product 68\n31,Product 31\n24,Product 24\n17,Product 17\n5,Smart Home Security System\n48,Product 48\n89,Product 89\n21,Product 21\n58,Product 58\n55,Product 55\n11,Yoga Mat Premium\n93,Product 93\n85,Product 85\n96,Product 96\n77,Product 77\n64,Product 64\n99,Product 99\n87,Product 87\n27,Product 27"
    },
    {
        "question": "Show the average rating for each product that has at least 5 reviews.",
        "sql": "SELECT p.product_id, p.name, AVG(r.rating) as avg_rating FROM products p JOIN product_reviews r ON p.product_id = r.product_id GROUP BY p.product_id, p.name HAVING COUNT(r.review_id) >= 5;",
        "expected_result": "(no rows)",
        "actual_result": "(no rows)"
    },
    {
        "question": "How many orders were placed in the last 30 days?",
        "sql": "SELECT COUNT(*) FROM orders WHERE order_date >= date('now', '-30 day');",
        "expected_result": "26",
        "actual_result": "26"
    },
    {
        "question": "List the top 3 offices by total inventory units.",
        "sql": "SELECT o.office_id, o.name, SUM(i.quantity) as total_units FROM offices o JOIN inventory i ON o.office_id = i.office_id GROUP BY o.office_id, o.name ORDER BY total_units DESC LIMIT 3;",
        "expected_result": "office_id,name,total_units\n7,Midwest Distribution Center,10089\n2,West Coast Office,9846\n3,European Headquarters,9650",
        "actual_result": "office_id,name,total_units\n7,Midwest Distribution Center,10089\n2,West Coast Office,9846\n3,European Headquarters,9650"
    },
    {
        "question": "Which customers have spent more than $1000 in total?",
        "sql": "SELECT c.customer_id, c.first_name, c.last_name, SUM(o.total_amount) as total_spent FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.first_name, c.last_name HAVING total_spent > 1000;",
        "expected_result": "customer_id,first_name,last_name,total_spent\n1,John,Smith,8182.8\n2,Maria,Garcia,6945.54\n3,James,Johnson,5664.32\n4,Emma,Brown,2450.78\n7,Hiroshi,Tanaka,2091.47\n8,Anna,Schmidt,1284.04\n9,Carlos,Rodriguez,2924.92\n10,Olivia,Wilson,6137.55\n11,Liu,Wei,4559.43\n12,Raj,Patel,4315.9\n13,Fatima,Al-Sayed,4253.26\n14,Isabella,Rossi,7964.39\n15,Michael,Davis,6185.8\n16,FirstName16,LastName16,3675.08\n17,FirstName17,LastName17,2027.3\n18,FirstName18,LastName18,2929.65\n19,FirstName19,LastName19,7419.61\n20,FirstName20,LastName20,9953.93\n21,FirstName21,LastName21,5042.52\n22,FirstName22,LastName22,10109.84\n23,FirstName23,LastName23,2070.14\n24,FirstName24,LastName24,7402.91\n26,FirstName26,LastName26,7189.72\n27,FirstName27,LastName27,3332.01\n28,FirstName28,LastName28,4349.46\n29,FirstName29,LastName29,1527.13\n31,FirstName31,LastName31,3485.04\n32,FirstName32,LastName32,1972.47\n33,FirstName33,LastName33,7342.94\n34,FirstName34,LastName34,10453.94\n35,FirstName35,LastName35,5980.12\n36,FirstName36,LastName36,3028.04\n37,FirstName37,LastName37,6031.55\n38,FirstName38,LastName38,1968.37\n40,FirstName40,LastName40,4399.26\n41,FirstName41,LastName41,3453.03\n42,FirstName42,LastName42,7446.35\n43,FirstName43,LastName43,2437.87\n44,FirstName44,LastName44,3240.27\n45,FirstName45,LastName45,7330.58\n46,FirstName46,LastName46,2312.91\n48,FirstName48,LastName48,2976.37\n49,FirstName49,LastName49,3713.73\n50,FirstName50,LastName50,3982.26",
        "actual_result": "customer_id,first_name,last_name,total_spent\n1,John,Smith,8182.8\n2,Maria,Garcia,6945.54\n3,James,Johnson,5664.32\n4,Emma,Brown,2450.78\n7,Hiroshi,Tanaka,2091.47\n8,Anna,Schmidt,1284.04\n9,Carlos,Rodriguez,2924.92\n10,Olivia,Wilson,6137.55\n11,Liu,Wei,4559.43\n12,Raj,Patel,4315.9\n13,Fatima,Al-Sayed,4253.26\n14,Isabella,Rossi,7964.39\n15,Michael,Davis,6185.8\n16,FirstName16,LastName16,3675.08\n17,FirstName17,LastName17,2027.3\n18,FirstName18,LastName18,2929.65\n19,FirstName19,LastName19,7419.61\n20,FirstName20,LastName20,9953.93\n21,FirstName21,LastName21,5042.52\n22,FirstName22,LastName22,10109.84\n23,FirstName23,LastName23,2070.14\n24,FirstName24,LastName24,7402.91\n26,FirstName26,LastName26,7189.72\n27,FirstName27,LastName27,3332.01\n28,FirstName28,LastName28,4349.46\n29,FirstName29,LastName29,1527.13\n31,FirstName31,LastName31,3485.04\n32,FirstName32,LastName32,1972.47\n33,FirstName33,LastName33,7342.94\n34,FirstName34,LastName34,10453.94\n35,FirstName35,LastName35,5980.12\n36,FirstName36,LastName36,3028.04\n37,FirstName37,LastName37,6031.55\n38,FirstName38,LastName38,1968.37\n40,FirstName40,LastName40,4399.26\n41,FirstName41,LastName41,3453.03\n42,FirstName42,LastName42,7446.35\n43,FirstName43,LastName43,2437.87\n44,FirstName44,LastName44,3240.27\n45,FirstName45,LastName45,7330.58\n46,FirstName46,LastName46,2312.91\n48,FirstName48,LastName48,2976.37\n49,FirstName49,LastName49,3713.73\n50,FirstName50,LastName50,3982.26"
    },
    {
        "question": "Find all products that are currently out of stock in all locations.",
        "sql": "SELECT p.product_id, p.name FROM products p WHERE NOT EXISTS (SELECT 1 FROM inventory i WHERE i.product_id = p.product_id AND i.quantity > 0);",
        "expected_result": "(no rows)",
        "actual_result": "(no rows)"
    },
    {
        "question": "What is the most common reason for product returns?",
        "sql": "SELECT return_reason, COUNT(*) as count FROM order_items WHERE status = 'returned' AND return_reason IS NOT NULL GROUP BY return_reason ORDER BY count DESC LIMIT 1;",
        "expected_result": "return_reason,count\nNot as described,7",
        "actual_result": "return_reason,count\nNot as described,7"
    }
]

# For demonstration, print all questions
if __name__ == "__main__":
    for q in questions:
        print(f"Q: {q['question']}\nSQL: {q['sql']}\nExpected: {q['expected_result']}\nActual: {q.get('actual_result', 'N/A')}\n") 