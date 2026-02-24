<?php
/**
 * PHP Login Integration Snippet for Campus Asset Tracker
 * ────────────────────────────────────────────────────────
 * This is what the PHP login page (index.php) needs to do
 * AFTER successfully authenticating the user.
 *
 * Place this logic inside your PHP login handler where you
 * currently redirect the user after a valid password check.
 */

// ── DB connection (adjust to your XAMPP config) ──────────────
$pdo = new PDO(
    'mysql:host=localhost;dbname=campus_asset_tracker;charset=utf8mb4',
    'root',
    '',   // default XAMPP blank password
    [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
);

/**
 * Call this function after verifying the user's credentials.
 * It creates a secure token, stores it in the shared DB table,
 * sets a cookie, and redirects to the Python Flask dashboard.
 *
 * @param int    $userId    The authenticated user's DB id
 * @param string $email     User email
 * @param string $fullName  User display name
 * @param string $role      'admin' | 'staff' | 'student'
 */
function loginAndRedirectToDashboard(PDO $pdo, int $userId, string $email, string $fullName, string $role): void
{
    // 1. Generate a cryptographically secure token
    $token = bin2hex(random_bytes(32));  // 64-char hex string

    // 2. Set expiry (8 hours from now)
    $expiresAt = date('Y-m-d H:i:s', strtotime('+8 hours'));

    // 3. Remove any old sessions for this user (one active session at a time)
    $pdo->prepare("DELETE FROM php_sessions WHERE user_id = ?")
        ->execute([$userId]);

    // 4. Write the new token to the shared session table
    $stmt = $pdo->prepare("
        INSERT INTO php_sessions (token, user_id, user_email, user_name, role, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ");
    $stmt->execute([$token, $userId, $email, $fullName, $role, $expiresAt]);

    // 5. Set the cookie (Python Flask reads this same cookie name)
    $cookieName = 'cat_session_token';
    setcookie(
        $cookieName,
        $token,
        [
            'expires'  => strtotime('+8 hours'),
            'path'     => '/',
            'httponly' => true,         // JS cannot read it
            'samesite' => 'Lax',        // CSRF protection
            // 'secure' => true,        // Uncomment when on HTTPS
        ]
    );

    // 6. Redirect to Python Flask dashboard
    //    Adjust port if you run Flask on a different port
    header('Location: http://localhost:5000/dashboard');
    exit();
}


// ══════════════════════════════════════════════
//  EXAMPLE USAGE inside your login handler
// ══════════════════════════════════════════════

/*
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email    = trim($_POST['email']    ?? '');
    $password = trim($_POST['password'] ?? '');

    // Look up user in DB
    $stmt = $pdo->prepare("SELECT * FROM users WHERE email = ? LIMIT 1");
    $stmt->execute([$email]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($user && password_verify($password, $user['password'])) {
        // ✅ Credentials valid – hand off to Python dashboard
        loginAndRedirectToDashboard(
            $pdo,
            (int)$user['id'],
            $user['email'],
            $user['full_name'],
            $user['role']
        );
    } else {
        $error = "Invalid email or password.";
    }
}
*/
?>
