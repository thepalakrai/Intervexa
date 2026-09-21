"""
Curated question bank for Virexa AI's Azure AI Search index.
Run upload_questions.py after this to push these into your search index.

Organized into broad professional categories rather than individual named
job titles - each category's questions apply naturally across several
related roles (e.g. "Nursing" covers Staff Nurse, ICU Nurse, general
Healthcare roles). This gives real breadth across industries without
pretending deep expertise in 50 hyper-specific titles.
"""

QUESTIONS = [
    # ============================================================
    # GENERAL HR / BEHAVIORAL (applies across every role)
    # ============================================================
    {"topic": "HR", "difficulty": 1, "text": "Tell me about yourself.",
     "expected_concepts": ["background", "relevant experience", "career motivation"]},
    {"topic": "HR", "difficulty": 1, "text": "Why do you want to work in this role?",
     "expected_concepts": ["role fit", "genuine interest", "career alignment"]},
    {"topic": "HR", "difficulty": 2, "text": "Tell me about a time you disagreed with a teammate. How did you resolve it?",
     "expected_concepts": ["conflict resolution", "communication", "compromise"]},
    {"topic": "HR", "difficulty": 2, "text": "Describe a project or task you're most proud of and why.",
     "expected_concepts": ["ownership", "impact", "specific contribution"]},
    {"topic": "HR", "difficulty": 2, "text": "How do you prioritize tasks when working on multiple things at once?",
     "expected_concepts": ["time management", "prioritization framework", "communication with stakeholders"]},
    {"topic": "HR", "difficulty": 3, "text": "Tell me about a time you made a mistake at work. What did you do?",
     "expected_concepts": ["accountability", "root cause", "corrective action"]},
    {"topic": "HR", "difficulty": 1, "text": "Where do you see yourself in three years?",
     "expected_concepts": ["career growth", "realistic goals", "alignment with role"]},
    {"topic": "HR", "difficulty": 2, "text": "How do you handle receiving critical feedback on your work?",
     "expected_concepts": ["openness to feedback", "growth mindset", "specific example"]},
    {"topic": "HR", "difficulty": 2, "text": "Describe a time you had to work under significant pressure or a tight deadline.",
     "expected_concepts": ["stress management", "prioritization", "outcome"]},
    {"topic": "HR", "difficulty": 3, "text": "Tell me about a time you had to persuade someone who initially disagreed with you.",
     "expected_concepts": ["persuasion", "evidence-based argument", "outcome"]},

    # ============================================================
    # SQL
    # ============================================================
    {"topic": "SQL", "difficulty": 1, "text": "What is the difference between WHERE and HAVING clauses?",
     "expected_concepts": ["WHERE filters rows before grouping", "HAVING filters after GROUP BY", "aggregate functions"]},
    {"topic": "SQL", "difficulty": 1, "text": "Explain the difference between INNER JOIN and LEFT JOIN.",
     "expected_concepts": ["INNER JOIN returns matching rows only", "LEFT JOIN keeps all left table rows", "NULLs for unmatched"]},
    {"topic": "SQL", "difficulty": 2, "text": "What is a primary key vs a foreign key?",
     "expected_concepts": ["primary key uniquely identifies a row", "foreign key references another table", "referential integrity"]},
    {"topic": "SQL", "difficulty": 2, "text": "Write a query to find the second-highest salary from an Employees table.",
     "expected_concepts": ["subquery or LIMIT/OFFSET", "DISTINCT", "ORDER BY"]},
    {"topic": "SQL", "difficulty": 3, "text": "What's the difference between a clustered and non-clustered index?",
     "expected_concepts": ["clustered index determines physical row order", "non-clustered index is a separate structure", "impact on read/write performance"]},
    {"topic": "SQL", "difficulty": 3, "text": "You have a table with duplicate rows. How would you identify and remove them?",
     "expected_concepts": ["GROUP BY / ROW_NUMBER()", "DELETE with subquery", "defining what counts as duplicate"]},
    {"topic": "SQL", "difficulty": 4, "text": "Explain how query execution plans work and how you'd use one to optimize a slow query.",
     "expected_concepts": ["EXPLAIN / execution plan", "identifying full table scans", "index usage"]},
    {"topic": "SQL", "difficulty": 2, "text": "What is normalization, and why is it used?",
     "expected_concepts": ["reducing data redundancy", "1NF/2NF/3NF", "data integrity"]},
    {"topic": "SQL", "difficulty": 3, "text": "Given a table with StudentID, StudentName, CourseID, CourseName - what normalization problem could occur here?",
     "expected_concepts": ["update anomaly", "redundant CourseName per row", "splitting into separate tables"]},
    {"topic": "SQL", "difficulty": 2, "text": "What's the difference between UNION and UNION ALL?",
     "expected_concepts": ["UNION removes duplicates", "UNION ALL keeps duplicates", "performance implications"]},

    # ============================================================
    # PYTHON
    # ============================================================
    {"topic": "Python", "difficulty": 1, "text": "What is the difference between a list and a tuple in Python?",
     "expected_concepts": ["lists are mutable", "tuples are immutable", "use cases for each"]},
    {"topic": "Python", "difficulty": 2, "text": "How would you handle missing values in a pandas DataFrame?",
     "expected_concepts": ["dropna()", "fillna()", "deciding based on context/data type"]},
    {"topic": "Python", "difficulty": 2, "text": "What's the difference between loc and iloc in pandas?",
     "expected_concepts": ["loc uses labels", "iloc uses integer positions", "example use case"]},
    {"topic": "Python", "difficulty": 3, "text": "Explain how you would merge two DataFrames with different key column names.",
     "expected_concepts": ["pd.merge with left_on/right_on", "join type (inner/outer/left)", "handling mismatched keys"]},
    {"topic": "Python", "difficulty": 3, "text": "What is the difference between a shallow copy and a deep copy?",
     "expected_concepts": ["shallow copy references nested objects", "deep copy fully duplicates", "copy module / deepcopy()"]},
    {"topic": "Python", "difficulty": 2, "text": "How do list comprehensions work, and why might you use one instead of a for loop?",
     "expected_concepts": ["concise syntax", "readability", "performance for simple transformations"]},
    {"topic": "Python", "difficulty": 4, "text": "How would you optimize a pandas operation that's running slowly on a large dataset?",
     "expected_concepts": ["vectorization over apply/loops", "avoiding iterrows", "chunking or dtype optimization"]},
    {"topic": "Python", "difficulty": 1, "text": "What is a dictionary in Python and when would you use one?",
     "expected_concepts": ["key-value pairs", "fast lookups", "use case example"]},

    # ============================================================
    # DATA ANALYSIS / STATISTICS
    # ============================================================
    {"topic": "Data Analysis", "difficulty": 2,
     "text": "Can you describe a situation where you had to analyze a dataset? What steps did you take to ensure your analysis was accurate and meaningful?",
     "expected_concepts": ["data cleaning", "validation steps", "clear conclusion tied to a business question"]},
    {"topic": "Data Analysis", "difficulty": 2, "text": "What steps would you take to clean a messy dataset before analysis?",
     "expected_concepts": ["handling missing values", "removing duplicates", "checking data types/outliers"]},
    {"topic": "Data Analysis", "difficulty": 3, "text": "How do you decide which chart type to use for a given dataset?",
     "expected_concepts": ["matching chart to data type", "categorical vs numerical", "avoiding misleading visuals"]},
    {"topic": "Data Analysis", "difficulty": 3, "text": "What is the difference between correlation and causation, and why does it matter in analysis?",
     "expected_concepts": ["correlation doesn't imply causation", "confounding variables", "example of a misleading correlation"]},
    {"topic": "Data Analysis", "difficulty": 2, "text": "What is an outlier, and how would you decide whether to remove one from your analysis?",
     "expected_concepts": ["definition of an outlier", "statistical vs domain judgment", "impact on results"]},
    {"topic": "Data Analysis", "difficulty": 4, "text": "How would you design an A/B test to measure the impact of a new feature?",
     "expected_concepts": ["control vs treatment group", "sample size/significance", "avoiding confounding factors"]},
    {"topic": "Data Analysis", "difficulty": 3, "text": "Explain the difference between mean, median, and mode, and when each is most useful.",
     "expected_concepts": ["definitions", "sensitivity to outliers", "appropriate use cases"]},
    {"topic": "Data Analysis", "difficulty": 3, "text": "What is statistical significance, and how would you explain a p-value to a non-technical stakeholder?",
     "expected_concepts": ["p-value definition", "significance threshold", "plain-language explanation"]},
    {"topic": "Data Analysis", "difficulty": 2, "text": "How would you present your findings to a stakeholder with no technical background?",
     "expected_concepts": ["simplifying jargon", "visualizations over raw numbers", "focusing on business impact"]},
    {"topic": "Data Analysis", "difficulty": 4, "text": "How would you detect and handle bias in a dataset before drawing conclusions from it?",
     "expected_concepts": ["sampling bias", "representation checks", "mitigation strategies"]},

    # ============================================================
    # DBMS
    # ============================================================
    {"topic": "DBMS", "difficulty": 2, "text": "Explain normalization in DBMS.",
     "expected_concepts": ["reducing redundancy", "1NF/2NF/3NF", "data integrity"]},
    {"topic": "DBMS", "difficulty": 2, "text": "What is a transaction, and what do the ACID properties mean?",
     "expected_concepts": ["Atomicity", "Consistency", "Isolation", "Durability"]},
    {"topic": "DBMS", "difficulty": 3, "text": "What is the difference between OLTP and OLAP systems?",
     "expected_concepts": ["OLTP for transactional workloads", "OLAP for analytical workloads", "example use cases"]},
    {"topic": "DBMS", "difficulty": 3, "text": "What is a deadlock in a database, and how can it be avoided?",
     "expected_concepts": ["circular resource wait", "lock ordering", "timeout/detection mechanisms"]},
    {"topic": "DBMS", "difficulty": 2, "text": "What is the difference between a database and a data warehouse?",
     "expected_concepts": ["operational vs analytical purpose", "schema differences", "typical use cases"]},
    {"topic": "DBMS", "difficulty": 4, "text": "How would you design a schema for a system that needs to track user orders and order items efficiently?",
     "expected_concepts": ["separate orders/order_items tables", "foreign key relationships", "normalization trade-offs"]},

    # ============================================================
    # SOFTWARE ENGINEERING (Java / DSA) - covers SDE / Backend Developer roles
    # ============================================================
    {"topic": "Java", "difficulty": 2, "text": "Explain how HashMap works internally in Java.",
     "expected_concepts": ["hashing", "buckets", "collision handling", "hashCode/equals"]},
    {"topic": "Java", "difficulty": 3, "text": "What happens when two keys have the same hash in a HashMap?",
     "expected_concepts": ["collision", "chaining/treeification", "equals() comparison"]},
    {"topic": "Java", "difficulty": 2, "text": "What is the difference between an ArrayList and a LinkedList?",
     "expected_concepts": ["array-backed vs node-backed", "access time trade-offs", "insertion/deletion cost"]},
    {"topic": "Java", "difficulty": 2, "text": "What is the difference between an abstract class and an interface in Java?",
     "expected_concepts": ["multiple inheritance via interfaces", "partial implementation in abstract classes", "when to use each"]},
    {"topic": "Java", "difficulty": 3, "text": "Explain the concept of garbage collection in Java.",
     "expected_concepts": ["automatic memory management", "generational GC", "when objects become eligible"]},
    {"topic": "DSA", "difficulty": 2, "text": "What is the time complexity of binary search, and what precondition does it require?",
     "expected_concepts": ["O(log n)", "sorted array requirement", "divide and conquer"]},
    {"topic": "DSA", "difficulty": 3, "text": "How would you detect a cycle in a linked list?",
     "expected_concepts": ["Floyd's cycle detection (slow/fast pointers)", "hash set approach", "time/space trade-offs"]},
    {"topic": "DSA", "difficulty": 3, "text": "Explain the difference between a stack and a queue, with a real-world use case for each.",
     "expected_concepts": ["LIFO vs FIFO", "stack use case (undo, call stack)", "queue use case (task scheduling)"]},
    {"topic": "DSA", "difficulty": 4, "text": "Given an array of integers, how would you find two numbers that add up to a target value, efficiently?",
     "expected_concepts": ["hashmap approach for O(n)", "brute force O(n^2) baseline", "trade-off explanation"]},
    {"topic": "DSA", "difficulty": 2, "text": "What is recursion, and what is a base case?",
     "expected_concepts": ["function calling itself", "base case to stop recursion", "stack usage"]},

    # ============================================================
    # HEALTHCARE / NURSING
    # ============================================================
    {"topic": "Nursing", "difficulty": 1, "text": "Why did you choose a career in nursing/healthcare?",
     "expected_concepts": ["genuine motivation", "patient care values", "personal connection"]},
    {"topic": "Nursing", "difficulty": 2, "text": "Describe a time you had to handle a difficult or distressed patient or family member.",
     "expected_concepts": ["empathy", "de-escalation", "professionalism under stress"]},
    {"topic": "Nursing", "difficulty": 2, "text": "How do you prioritize care when you have multiple patients needing attention at once?",
     "expected_concepts": ["triage/prioritization by severity", "time management", "teamwork with colleagues"]},
    {"topic": "Nursing", "difficulty": 3, "text": "Walk me through the steps you'd take if you noticed a medication error was about to happen.",
     "expected_concepts": ["stopping the error", "verification protocols", "reporting/documentation"]},
    {"topic": "Nursing", "difficulty": 2, "text": "How do you ensure patient confidentiality and privacy in your daily work?",
     "expected_concepts": ["HIPAA/privacy principles", "secure handling of records", "discretion in conversations"]},
    {"topic": "Nursing", "difficulty": 3, "text": "How do you stay calm and effective during a medical emergency?",
     "expected_concepts": ["following protocol", "clear communication with team", "staying composed under pressure"]},
    {"topic": "Nursing", "difficulty": 2, "text": "How do you communicate complex medical information to a patient or family in a way they can understand?",
     "expected_concepts": ["avoiding jargon", "checking understanding", "empathy in delivery"]},
    {"topic": "Nursing", "difficulty": 1, "text": "What does patient-centered care mean to you?",
     "expected_concepts": ["individualized care", "respecting patient preferences", "holistic approach"]},

    # ============================================================
    # FINANCE / ACCOUNTING / BANKING
    # ============================================================
    {"topic": "Finance", "difficulty": 1, "text": "What interests you about working in finance/accounting?",
     "expected_concepts": ["genuine motivation", "analytical interest", "career alignment"]},
    {"topic": "Finance", "difficulty": 2, "text": "What is the difference between a balance sheet and an income statement?",
     "expected_concepts": ["balance sheet shows financial position at a point in time", "income statement shows performance over a period", "what each includes"]},
    {"topic": "Finance", "difficulty": 2, "text": "Explain the concept of accounts payable vs accounts receivable.",
     "expected_concepts": ["AP = money owed by the company", "AR = money owed to the company", "impact on cash flow"]},
    {"topic": "Finance", "difficulty": 3, "text": "How would you detect a discrepancy while reconciling two financial statements?",
     "expected_concepts": ["systematic comparison", "identifying timing differences", "documentation of findings"]},
    {"topic": "Finance", "difficulty": 3, "text": "What is the time value of money, and why does it matter in financial decision-making?",
     "expected_concepts": ["money today is worth more than in future", "discounting/present value", "application in investment decisions"]},
    {"topic": "Finance", "difficulty": 2, "text": "How would you explain a budget variance to a non-financial manager?",
     "expected_concepts": ["plain-language explanation", "actual vs budgeted comparison", "root cause of variance"]},
    {"topic": "Finance", "difficulty": 4, "text": "How would you assess whether a company is in good financial health using its financial statements?",
     "expected_concepts": ["liquidity ratios", "profitability ratios", "debt/leverage ratios"]},
    {"topic": "Finance", "difficulty": 2, "text": "What steps would you take if you found an error in a client's financial records?",
     "expected_concepts": ["verification before acting", "proper correction process", "communication with relevant parties"]},

    # ============================================================
    # MECHANICAL ENGINEERING
    # ============================================================
    {"topic": "Mechanical Engineering", "difficulty": 2, "text": "Explain the difference between stress and strain in materials.",
     "expected_concepts": ["stress = force per unit area", "strain = deformation relative to original size", "relationship via elasticity"]},
    {"topic": "Mechanical Engineering", "difficulty": 2, "text": "What is the difference between kinetic and potential energy, with a real-world example?",
     "expected_concepts": ["definitions", "conservation of energy", "practical example"]},
    {"topic": "Mechanical Engineering", "difficulty": 3, "text": "Walk me through how you would approach diagnosing a mechanical failure in a system.",
     "expected_concepts": ["systematic root-cause analysis", "inspection/testing steps", "documentation"]},
    {"topic": "Mechanical Engineering", "difficulty": 3, "text": "What factors would you consider when selecting a material for a load-bearing component?",
     "expected_concepts": ["strength requirements", "cost", "environmental/corrosion resistance"]},
    {"topic": "Mechanical Engineering", "difficulty": 2, "text": "What is the purpose of a factor of safety in mechanical design?",
     "expected_concepts": ["margin against failure", "accounting for uncertainty", "typical application"]},
    {"topic": "Mechanical Engineering", "difficulty": 4, "text": "How would you approach optimizing a design for both cost and performance?",
     "expected_concepts": ["trade-off analysis", "iterative design/testing", "balancing constraints"]},

    # ============================================================
    # CIVIL ENGINEERING
    # ============================================================
    {"topic": "Civil Engineering", "difficulty": 2, "text": "What factors would you consider when selecting a site for a construction project?",
     "expected_concepts": ["soil conditions", "environmental impact", "accessibility/logistics"]},
    {"topic": "Civil Engineering", "difficulty": 3, "text": "Explain the importance of load calculations in structural design.",
     "expected_concepts": ["dead load vs live load", "safety margins", "consequences of miscalculation"]},
    {"topic": "Civil Engineering", "difficulty": 2, "text": "What steps would you take to ensure quality control on a construction site?",
     "expected_concepts": ["material testing", "regular inspections", "adherence to specifications"]},
    {"topic": "Civil Engineering", "difficulty": 3, "text": "How would you handle a situation where a project is falling behind schedule?",
     "expected_concepts": ["identifying bottlenecks", "resource reallocation", "stakeholder communication"]},
    {"topic": "Civil Engineering", "difficulty": 2, "text": "What is the difference between reinforced concrete and plain concrete, and why does it matter?",
     "expected_concepts": ["tensile strength via rebar", "use cases", "structural implications"]},

    # ============================================================
    # ELECTRICAL ENGINEERING
    # ============================================================
    {"topic": "Electrical Engineering", "difficulty": 2, "text": "Explain Ohm's Law and its practical significance.",
     "expected_concepts": ["V = IR", "relationship between voltage, current, resistance", "practical application"]},
    {"topic": "Electrical Engineering", "difficulty": 2, "text": "What is the difference between AC and DC current?",
     "expected_concepts": ["AC alternates direction", "DC flows in one direction", "use cases for each"]},
    {"topic": "Electrical Engineering", "difficulty": 3, "text": "How would you troubleshoot a circuit that isn't functioning as expected?",
     "expected_concepts": ["systematic testing (multimeter)", "isolating the faulty component", "verifying against design"]},
    {"topic": "Electrical Engineering", "difficulty": 3, "text": "What safety precautions are essential when working with high-voltage systems?",
     "expected_concepts": ["lockout/tagout procedures", "PPE", "de-energizing before work"]},
    {"topic": "Electrical Engineering", "difficulty": 4, "text": "How would you approach designing a circuit to meet both power efficiency and cost constraints?",
     "expected_concepts": ["component selection trade-offs", "efficiency calculations", "iterative testing"]},

    # ============================================================
    # TEACHING / EDUCATION
    # ============================================================
    {"topic": "Teaching", "difficulty": 1, "text": "Why did you choose a career in teaching/education?",
     "expected_concepts": ["genuine motivation", "passion for the subject", "impact on students"]},
    {"topic": "Teaching", "difficulty": 2, "text": "How do you adapt your teaching style for students with different learning needs?",
     "expected_concepts": ["differentiated instruction", "recognizing individual needs", "specific example"]},
    {"topic": "Teaching", "difficulty": 2, "text": "Describe a time a lesson didn't go as planned. What did you do?",
     "expected_concepts": ["adaptability", "reflection", "adjustment mid-lesson"]},
    {"topic": "Teaching", "difficulty": 3, "text": "How do you handle a disruptive student in the classroom?",
     "expected_concepts": ["de-escalation", "consistent boundaries", "addressing root cause"]},
    {"topic": "Teaching", "difficulty": 2, "text": "How do you assess whether students have actually understood a concept, beyond just test scores?",
     "expected_concepts": ["formative assessment", "in-class questioning", "practical application checks"]},
    {"topic": "Teaching", "difficulty": 3, "text": "How would you communicate a student's struggles to a concerned parent?",
     "expected_concepts": ["clear and empathetic communication", "focus on constructive next steps", "collaboration with parent"]},
    {"topic": "Teaching", "difficulty": 2, "text": "How do you keep students engaged during a long or challenging lesson?",
     "expected_concepts": ["interactive techniques", "varying activities", "relating content to real life"]},

    # ============================================================
    # AVIATION / OPERATIONS
    # ============================================================
    {"topic": "Aviation", "difficulty": 1, "text": "Why are you interested in a career in aviation?",
     "expected_concepts": ["genuine motivation", "interest in the industry", "career fit"]},
    {"topic": "Aviation", "difficulty": 2, "text": "How would you handle an anxious or difficult passenger during a flight?",
     "expected_concepts": ["calm communication", "de-escalation", "following safety protocol"]},
    {"topic": "Aviation", "difficulty": 3, "text": "Describe how you would respond in an emergency situation onboard.",
     "expected_concepts": ["following trained procedures", "staying calm", "clear communication with crew/passengers"]},
    {"topic": "Aviation", "difficulty": 2, "text": "How do you ensure strict adherence to safety checklists and procedures under time pressure?",
     "expected_concepts": ["discipline in following checklists", "not skipping steps despite pressure", "double-checking critical items"]},
    {"topic": "Aviation", "difficulty": 2, "text": "How would you handle a scheduling conflict or last-minute operational change?",
     "expected_concepts": ["adaptability", "clear communication with team", "prioritizing safety/compliance"]},
    {"topic": "Aviation", "difficulty": 3, "text": "What steps would you take if you noticed a safety concern that others seemed to be overlooking?",
     "expected_concepts": ["speaking up despite hierarchy", "following reporting procedures", "prioritizing safety over convenience"]},

    # ============================================================
    # HR / RECRUITMENT
    # ============================================================
    {"topic": "HR Recruitment", "difficulty": 2, "text": "How would you evaluate whether a candidate is a good cultural fit for a team?",
     "expected_concepts": ["behavioral interview techniques", "alignment with values", "avoiding bias"]},
    {"topic": "HR Recruitment", "difficulty": 2, "text": "How do you handle a situation where a hiring manager wants to reject a strong candidate for a vague reason?",
     "expected_concepts": ["asking clarifying questions", "advocating with data", "balancing manager's authority and fairness"]},
    {"topic": "HR Recruitment", "difficulty": 3, "text": "Describe a time you had to resolve a conflict between two employees.",
     "expected_concepts": ["neutral mediation", "listening to both sides", "fair resolution"]},
    {"topic": "HR Recruitment", "difficulty": 2, "text": "How would you handle a confidential employee complaint about a manager?",
     "expected_concepts": ["confidentiality", "proper investigation process", "protecting the employee from retaliation"]},
    {"topic": "HR Recruitment", "difficulty": 3, "text": "How do you stay updated on employment law and ensure company policies remain compliant?",
     "expected_concepts": ["continuous learning", "legal resource use", "policy review process"]},

    # ============================================================
    # CUSTOMER SERVICE
    # ============================================================
    {"topic": "Customer Service", "difficulty": 1, "text": "What does great customer service mean to you?",
     "expected_concepts": ["empathy", "responsiveness", "problem resolution"]},
    {"topic": "Customer Service", "difficulty": 2, "text": "Describe a time you dealt with an angry or upset customer. How did you resolve it?",
     "expected_concepts": ["active listening", "de-escalation", "resolution focus"]},
    {"topic": "Customer Service", "difficulty": 2, "text": "How do you handle a situation where you can't give the customer exactly what they want?",
     "expected_concepts": ["honest communication", "offering alternatives", "managing expectations"]},
    {"topic": "Customer Service", "difficulty": 3, "text": "How do you balance following company policy with doing what's best for the customer?",
     "expected_concepts": ["judgment within policy limits", "escalation when needed", "customer-centric thinking"]},
    {"topic": "Customer Service", "difficulty": 2, "text": "How do you handle multiple customer requests at the same time?",
     "expected_concepts": ["prioritization", "clear communication of wait times", "staying organized"]},

    # ============================================================
    # MARKETING
    # ============================================================
    {"topic": "Marketing", "difficulty": 2, "text": "How would you measure the success of a marketing campaign?",
     "expected_concepts": ["defining KPIs upfront", "ROI/conversion tracking", "comparing against goals"]},
    {"topic": "Marketing", "difficulty": 2, "text": "How do you identify and understand a target audience for a new product?",
     "expected_concepts": ["market research", "customer segmentation", "persona development"]},
    {"topic": "Marketing", "difficulty": 3, "text": "Describe a marketing campaign you worked on that didn't perform as expected. What did you learn?",
     "expected_concepts": ["honest reflection", "root cause analysis", "actionable learning"]},
    {"topic": "Marketing", "difficulty": 3, "text": "How would you approach marketing a product with a very limited budget?",
     "expected_concepts": ["prioritizing high-impact channels", "organic/low-cost tactics", "creative resourcefulness"]},
    {"topic": "Marketing", "difficulty": 2, "text": "How do you stay current with changing trends in digital marketing?",
     "expected_concepts": ["continuous learning", "following industry sources", "experimentation"]},

    # ============================================================
    # SALES
    # ============================================================
    {"topic": "Sales", "difficulty": 2, "text": "Walk me through how you would approach a cold prospect who isn't interested initially.",
     "expected_concepts": ["understanding their needs", "value-based pitch", "handling rejection gracefully"]},
    {"topic": "Sales", "difficulty": 2, "text": "How do you handle objections from a potential customer during a sales pitch?",
     "expected_concepts": ["active listening", "addressing the real concern", "not being pushy"]},
    {"topic": "Sales", "difficulty": 3, "text": "Describe a time you lost a big deal. What did you learn from it?",
     "expected_concepts": ["honest reflection", "identifying what went wrong", "applying the lesson going forward"]},
    {"topic": "Sales", "difficulty": 2, "text": "How do you build long-term trust with a client rather than just closing a one-time sale?",
     "expected_concepts": ["relationship-building", "follow-through", "customer success focus"]},
    {"topic": "Sales", "difficulty": 3, "text": "How do you prioritize your pipeline when you have many leads at different stages?",
     "expected_concepts": ["lead scoring/prioritization", "time management", "focus on highest-probability deals"]},

    # ============================================================
    # HOSPITALITY
    # ============================================================
    {"topic": "Hospitality", "difficulty": 1, "text": "Why are you drawn to a career in hospitality?",
     "expected_concepts": ["genuine motivation", "enjoyment of guest interaction", "service orientation"]},
    {"topic": "Hospitality", "difficulty": 2, "text": "Describe a time you went above and beyond for a guest.",
     "expected_concepts": ["initiative", "attention to guest needs", "positive outcome"]},
    {"topic": "Hospitality", "difficulty": 2, "text": "How would you handle a guest complaint about their room or service?",
     "expected_concepts": ["active listening", "prompt resolution", "following up to ensure satisfaction"]},
    {"topic": "Hospitality", "difficulty": 3, "text": "How do you manage a high-pressure situation during peak hours with multiple guest needs?",
     "expected_concepts": ["prioritization", "staying composed", "teamwork"]},

    # ============================================================
    # LEGAL
    # ============================================================
    {"topic": "Legal", "difficulty": 2, "text": "How do you ensure accuracy and attention to detail when reviewing legal documents?",
     "expected_concepts": ["systematic review process", "double-checking critical clauses", "awareness of consequences of errors"]},
    {"topic": "Legal", "difficulty": 2, "text": "How would you explain a complex legal concept to a client with no legal background?",
     "expected_concepts": ["plain-language explanation", "avoiding jargon", "checking client understanding"]},
    {"topic": "Legal", "difficulty": 3, "text": "How do you handle confidential client information, especially in a busy office environment?",
     "expected_concepts": ["strict confidentiality practices", "secure document handling", "discretion"]},
    {"topic": "Legal", "difficulty": 3, "text": "Describe how you would approach researching a legal question you're unfamiliar with.",
     "expected_concepts": ["systematic legal research", "using reliable sources", "verifying with precedent/statute"]},

    # ============================================================
    # RETAIL / OPERATIONS
    # ============================================================
    {"topic": "Retail Operations", "difficulty": 1, "text": "What do you think makes for a great in-store customer experience?",
     "expected_concepts": ["friendly service", "store presentation", "efficient checkout"]},
    {"topic": "Retail Operations", "difficulty": 2, "text": "How would you handle a situation where inventory counts don't match the system?",
     "expected_concepts": ["systematic recount", "identifying discrepancy source", "documentation/reporting"]},
    {"topic": "Retail Operations", "difficulty": 2, "text": "How do you manage a busy shift with limited staff?",
     "expected_concepts": ["prioritization", "delegating effectively", "staying calm under pressure"]},
    {"topic": "Retail Operations", "difficulty": 3, "text": "Describe how you would train a new team member on store procedures.",
     "expected_concepts": ["structured onboarding", "hands-on practice", "checking for understanding"]},

    # ============================================================
    # PROJECT / RESUME-BASED (generic prompts the interviewer adapts using real project names)
    # ============================================================
    {"topic": "Project", "difficulty": 2, "text": "Walk me through a project on your resume that you're proud of. What was your specific contribution?",
     "expected_concepts": ["clear ownership", "technical/practical decisions made", "outcome/impact"]},
    {"topic": "Project", "difficulty": 3, "text": "What was the most challenging part of a project you've worked on, and how did you solve it?",
     "expected_concepts": ["specific obstacle", "problem-solving approach", "result"]},
    {"topic": "Project", "difficulty": 3, "text": "If you had more time on one of your past projects, what would you improve and why?",
     "expected_concepts": ["self-awareness of limitations", "specific improvement idea", "reasoning"]},
]
