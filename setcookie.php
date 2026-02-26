<?php
setcookie('cat_session_token', 'dev_token_admin', [
    'expires'  => time() + (8 * 60 * 60),
    'path'     => '/',
    'httponly' => true,
    'samesite' => 'Lax',
]);
header('Location: /dashboard/dashboard.py');
exit();
?>
