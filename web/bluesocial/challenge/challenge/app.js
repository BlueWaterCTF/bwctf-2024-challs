const express = require('express');
const cookieParser = require('cookie-parser');
const crypto = require('crypto');
const { rateLimit } = require("express-rate-limit");
const bot = require("./bot");

const PORT = process.env.PORT || 1337;

const app = express();

// Middleware
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(express.json());
app.use('/static', express.static('static'))

// In-memory storage
const users = {};

// Authentication middleware
function authenticateUser(req, res, next) {
    const { username } = req.cookies;
    if (!username || !users[username]) {
        return res.redirect('/login');
    }
    if(!isValidUsername(username)) return res.sendStatus(400);
    req.username = username;
    next();
}

// Username validation function
function isValidUsername(username) {
    return /^[A-Za-z0-9]+$/.test(username);
}

// HTML templates
function getNavBar(username) {
    let navItems = `
        <a href="/login">Login</a>
    `;
    if (username) {
        navItems = `
            <a href="/user/home">Home</a> |
            <a href="/logout">Logout</a>
        `;
    }
    return `
    <nav style="background-color: #f2f2f2; padding: 10px; margin-bottom: 20px;">
        <h1 style="margin: 0;"><a href="/" style="text-decoration: none; color: black;">Transient Social App</a></h1>
        <div>${navItems}</div>
    </nav>
    `;
}

function wrapWithLayout(content, username) {
    return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Transient Social App</title>
    </head>
    <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
        ${getNavBar(username)}
        ${content}
    </body>
    </html>
    `;
}

const loginForm = `
<h2>Login</h2>
<form action="/login" method="post">
    <input type="text" name="username" placeholder="Username" required pattern="[A-Za-z0-9]+" title="Username must contain only letters and numbers"><br>
    <button type="submit">Login</button>
</form>
`;

// CSP middleware with strict inline script policy

function DefaultMiddleware(req, res, next){
    res.setHeader('X-Frame-Options', 'SAMEORIGIN');
    res.set('Content-Type', 'text/html')
    next();
}

app.use(DefaultMiddleware);

// Routes
app.get('/', (req, res, next) => {
    res.send(wrapWithLayout(`<h2>Welcome to Transient Social App</h2>
    <p>Please <a href="/login">login</a> to continue.</p>`, req.cookies.username));
    next();
});

app.get('/login', (req, res, next) => {
    res.send(wrapWithLayout(loginForm, req.cookies.username));
    next();
});

app.post('/login', (req, res, next) => {
    const { username } = req.body;
    
    if (!isValidUsername(username)) {
        return res.status(400).send(wrapWithLayout('Invalid username format', null));
    }

    // Create user if it doesn't exist
    if (!users[username]) {
        users[username] = { bio: '' };
    }

    res.cookie('username', username, { httpOnly: true, maxAge: 3600000 }); // 1 hour
    res.redirect('/user/home');
    next();
});

app.get('/logout', authenticateUser, (req, res, next) => {
    const { username } = req.cookies;
    if (username) {
        delete users[username]; // Delete user data on logout
    }
    res.clearCookie('username');
    res.redirect('/login');
    next();
});

app.post('/user/update', authenticateUser, (req, res, next) => {
    const { bio } = req.body;
    if (bio !== undefined) {
        users[req.username].bio = bio.toString();
    }
    res.redirect('/user/home');
    next();
});

app.get('/user/:username', (req, res, next) => {
    const { username } = req.params;
    const user = users[username];

    if (user) {
        //no hacc pls
        res.setHeader('Content-Security-Policy',`default-src 'self';`);
        return res.send({ username, bio: user.bio });
    }
    next();
});

app.get('/user/home', authenticateUser, (req, res, next) => {
    const content = `
        <h2>Welcome to Transient Social App, ${req.username}!</h2>
        <p><strong>Your bio:</strong> <span id="userBio">Loading...</span></p>
        <h3>Update Your Bio</h3>
        <form id="updateBioForm">
            <textarea id="bioInput" name="bio" placeholder="Enter your bio"></textarea><br>
            <button type="submit">Update Bio</button>
        </form>
        <iframe id="dompurifyFrame" src="/dompurify" style="display: none;"></iframe>
        <script src="/static/home.js"></script>
        <script>
            window.addEventListener('hashchange', userUpdate);
            window.addEventListener('load', function(){
                init("${req.username}");
            });
        </script>
    `;
    res.send(wrapWithLayout(content, req.username));
    next();
});

app.get('/dompurify', (req, res, next) => {
    const content = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
    </head>
    <body>
        <script type=module src="/static/purify.js"></script>
    </body>
    </html>
    `;
    res.send(content);
    next();
});

// thank you strellic
app.get("/report", rateLimit({ windowMs: 60_000, limit: 3, message: "you are reporting too fast, please slow down!", skipFailedRequests: true }), async (req, res) => {

    const { url } = req.query;
    if (typeof url !== "string") {
        return res.status(400).send("missing url");
    }

    let u;
    try {
        u = new URL(url);
    } catch {
        return res.status(400).send("invalid url");
    }

    if (u.protocol !== "http:" && u.protocol !== "https:") {
        return res.status(400).send("url must either be http: or https:");
    }

    try {
        res.send(await bot.visit(url));
    }
    catch (err) {
        res.status(400).send(err.message);
    }
});


app.listen(PORT, () => console.log(`Transient Social App running on port ${PORT}`));
