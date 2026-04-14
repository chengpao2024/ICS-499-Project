<?php
session_start();
// If already logged in with a valid session, go straight to dashboard
if (isset($_SESSION['user'], $_SESSION['role'], $_SESSION['user_id'])) {
    header("Location: /dashboard/dashboard.py");
    exit();
}

require_once __DIR__ . '/config/db.php';

$error = "";

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $identifier = trim($_POST['username'] ?? '');
    $password   = $_POST['password'] ?? '';

    $user = null;
    $role = null;

    // Try admins table (matches on admin_username)
    $stmt = $conn->prepare(
        "SELECT admin_id, admin_username, admin_password
         FROM admins WHERE admin_username = ? LIMIT 1"
    );
    $stmt->bind_param('s', $identifier);
    $stmt->execute();
    $row = $stmt->get_result()->fetch_assoc();
    $stmt->close();

    if ($row && password_verify($password, $row['admin_password'])) {
        $user = [
            'id'           => $row['admin_id'],
            'display_name' => $row['admin_username'],
            'identifier'   => $row['admin_username'],
        ];
        $role = 'admin';
    }

    // Try faculty table (matches on faculty_email)
    if (!$user) {
        $stmt = $conn->prepare(
            "SELECT faculty_id, faculty_fname, faculty_lname,
                    faculty_email, faculty_password
             FROM faculty WHERE faculty_email = ? LIMIT 1"
        );
        $stmt->bind_param('s', $identifier);
        $stmt->execute();
        $row = $stmt->get_result()->fetch_assoc();
        $stmt->close();

        if ($row && password_verify($password, $row['faculty_password'])) {
            $user = [
                'id'           => $row['faculty_id'],
                'display_name' => $row['faculty_fname'] . ' ' . $row['faculty_lname'],
                'identifier'   => $row['faculty_email'],
            ];
            $role = 'faculty';
        }
    }

    // Try students table (matches on student_email)
    if (!$user) {
        $stmt = $conn->prepare(
            "SELECT student_id, student_fname, student_lname,
                    student_email, student_password
             FROM students WHERE student_email = ? LIMIT 1"
        );
        $stmt->bind_param('s', $identifier);
        $stmt->execute();
        $row = $stmt->get_result()->fetch_assoc();
        $stmt->close();

        if ($row && password_verify($password, $row['student_password'])) {
            $user = [
                'id'           => $row['student_id'],
                'display_name' => $row['student_fname'] . ' ' . $row['student_lname'],
                'identifier'   => $row['student_email'],
            ];
            $role = 'student';
        }
    }

    // Login success
    if ($user && $role) {
        // Regenerate session ID to prevent session fixation attacks
        session_regenerate_id(true);

        $_SESSION['user']         = $user['identifier'];
        $_SESSION['user_id']      = $user['id'];
        $_SESSION['role']         = $role;
        $_SESSION['display_name'] = $user['display_name'];

        header("Location: ../dashboard/dashboard.py");
        exit();

    } else {
        $error = "Invalid username/email or password.";
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>CAT Login</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>

<div class="split-container" style="display:flex; height:100vh; width:100%;">

    <div class="left-panel" style="flex:1; overflow:hidden;">
        <img src="test.jpg" alt="Campus Asset Tracker" style="width:100%; height:100%; object-fit:cover;">
        <div class="acronym-overlay">
            <div class="acronym-line"><span class="acronym-letter">C</span><span class="acronym-word">ampus</span></div>
            <div class="acronym-line"><span class="acronym-letter">A</span><span class="acronym-word">sset</span></div>
            <div class="acronym-line"><span class="acronym-letter">T</span><span class="acronym-word">racker</span></div>
        </div>
    </div>

    <div class="right-panel" style="flex:1; display:flex; align-items:center; justify-content:center;">

        <div class="login-container">
            <h2>Campus Asset Tracker (CAT)</h2>
            <h3>Login</h3>

            <?php if ($error): ?>
                <p class="error"><?= htmlspecialchars($error) ?></p>
            <?php endif; ?>

            <form method="POST" action="">
                <input type="text"     name="username" placeholder="Username or Email" required>
                <input type="password" name="password" placeholder="Password"          required>
                <button type="submit">Login</button>
            </form>

            <!-- Test credentials (remove before production) -->
            <p style="font-size:11px; color:#999; margin-top:16px;">
                Admin: admin1 &nbsp;|&nbsp;
                Faculty: teacher1@gmail.com &nbsp;|&nbsp;
                Student: student1@gmail.com
            </p>
        </div>

    </div>

</div>

</body>
</html>