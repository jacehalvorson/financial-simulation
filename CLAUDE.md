# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A financial simulation web application built with PyWire that visualizes historical stock market performance across countries, inflation data, and provides tools for retirement planning (contributions, withdrawals, medical receipts).

## Development Commands

```bash
# Install/sync dependencies
uv sync

# Run development server (with hot-reload)
uv run pywire dev

# The dev server starts on http://localhost:8000 by default
```

## Architecture

### PyWire Framework

This project uses **PyWire**, a Python web framework with path-based routing. Key concepts:

- **Pages directory**: `src/pages/` - routes are automatically mapped from file structure
- **`.wire` files**: Combine Python logic and HTML templates in a single file
  - Python code goes at the top (before `--- html ---`)
  - HTML goes after the `--- html ---` separator
  - Python variables can be interpolated into HTML using `{variable_name}` syntax
- **Layouts**: `__layout__.wire` files define templates for nested routes
  - `src/pages/__layout__.wire` - root layout with navigation
  - `src/pages/dashboard/__layout__.wire` - dashboard-specific layout
  - Child pages are inserted via `<slot />` tag
- **PJAX enabled**: Partial page updates for faster navigation (configured in [main.py:6](src/main.py#L6))

### Route Structure

```
/                   -> src/pages/index.wire (landing page with feature cards)
/globalmarket       -> src/pages/globalmarket.wire (country stock market data)
/contributions      -> src/pages/contributions.wire (retirement contributions)
/withdrawals        -> src/pages/withdrawals.wire (retirement withdrawals)
/medicalreceipts    -> src/pages/medicalreceipts.wire (HSA receipts)
/pricing           -> src/pages/pricing.wire
/login             -> src/pages/login.wire
/dashboard/*       -> src/pages/dashboard/ (protected area)
```

### Data Layer

**Financial data utilities** ([financial_data.py](src/financial_data.py)):
- Fetches stock market data via yfinance API (`get_sp500_returns`, `get_us_total_market_returns`, `get_global_market_returns`)
- Provides inflation data with fallback to hardcoded values (`get_inflation_data`)
- Returns data as `{dates: [], values: []}` with compounded values starting at 1.0

**World Bank data utilities** ([worldbank_data.py](src/worldbank_data.py)):
- Loads S&P Global Equity Indices from CSV file in `data/` directory
- Provides country-specific stock market returns (`get_country_stock_returns`)
- Lists 84+ countries with available data (`get_available_countries`)
- Default focus countries defined in `DEFAULT_COUNTRIES` list

**Database models** ([models.py](src/models.py)):
- SQLAlchemy ORM with declarative base
- `User` model: email, created_at
- `Subscription` model: user_id, stripe_customer_id, status (linked to Stripe integration)

### Application Entry Point

[main.py](src/main.py) creates the PyWire application instance with:
- Pages directory: `src/pages`
- PJAX enabled for SPA-like behavior
- Debug mode on

## Data Files

World Bank stock market data is stored in `data/API_CM.MKT.INDX.ZG_DS2_en_csv_v2_10345.csv` containing S&P Global Equity Indices (annual percentage changes) for 84+ countries from 1960-2024.

## Styling

Uses Pico CSS (minimal classless CSS framework) loaded from CDN in the root layout.

## PyWire Context

This project uses a new Python web framework that is not widespread on the internet and is likely missing from most LLM training datasets. Here is some information provided by the documentation at [nightly.pywire.dev/docs](https://nightly.pywire.dev/docs).

```text
<SYSTEM>This is the full developer documentation for pywire</SYSTEM>

# pywire Docs

> HTML-over-the-wire without the JavaScript hangover.



# Server-Side Events

> Handling browser events in Python.

PyWire allows you to handle standard browser events (like clicks, inputs, and form submissions) directly in Python.

## Basic Event Handling

[Section titled “Basic Event Handling”](#basic-event-handling)

Use the `@` prefix followed by the event name to bind a Python function to a browser event.

```pywire
count = wire(0)


def handle_click():
    $count += 1


---html---
<button @click={handle_click}>
    Clicked {count.value} times
</button>
```

## Passing Data

[Section titled “Passing Data”](#passing-data)

You can pass data from the browser to your Python handlers.

```pywire
items = wire([{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}])


def delete_item(item_id):
    $items = [i for i in $items if i['id'] != item_id]


---html---
<ul>
    <li $for={item in items.value}>
        {item['name']}
        <button @click={delete_item(item['id'])}>Delete</button>
    </li>
</ul>
```

## Input Events

[Section titled “Input Events”](#input-events)

For input fields, you can use `@input` or `@change`.

```pywire
search_query = wire("")


def on_search(event):
    $search_query = event.value
    print(f"Searching for: {event.value}")


---html---
<input type="text"
       placeholder="Search..."
       @input={on_search}>
```

We’ll cover more advanced event features in the [Event Modifiers](/docs/syntax/event-modifiers) section.

# Reactivity & State

> Managing state with the wire primitive.

PyWire uses an explicit, opt-in reactivity model. Standard Python variables behave normally, while variables wrapped in `wire()` become reactive data sources that drive UI updates.

## The `wire()` Primitive

[Section titled “The wire() Primitive”](#the-wire-primitive)

To create reactive state, initialize a variable with `wire()`.

```python
from pywire import wire


# Reactive integer
count = wire(0)


# Reactive string
username = wire("Guest")


# Reactive namespace (dictionary-like)
user = wire(name="Alice", age=30, role="admin")
```

### Reading Values

[Section titled “Reading Values”](#reading-values)

You access the underlying value using the `.value` property. Only use this in Python snippets. In HTML, use the value directly such as `count`.

```python
print(count.value)
# Output: 0


print(user.name)
# Output: "Alice"
```

### Writing Values

[Section titled “Writing Values”](#writing-values)

Modifying the `.value` triggers the reactivity system. PyWire detects the change and marks any part of the template dependent on this variable as “dirty,” queuing it for an update.

```python
count.value = 5  # Triggers UI update
user.age = 31    # Triggers UI update
```

## The `$` Syntax Sugar

[Section titled “The $ Syntax Sugar”](#the--syntax-sugar)

To make your Python logic cleaner and more concise, `.wire` files support a special preprocessor syntax: the `$` prefix.

When you use `$` before a variable name inside the Python block of a `.wire` file, it automatically compiles to `.value`.

```python
# Your code in .wire file
def increment():
    $count += 1
    print(f"New count is {$count}")


# Compiled code
def increment(self):
    self.count.value += 1
    print(f"New count is {self.count.value}")
```

> \[!TIP] Use `$` for read/write operations inside your functions to keep your logic readable.

## Scope & Persistence

[Section titled “Scope & Persistence”](#scope--persistence)

### Component Scope

[Section titled “Component Scope”](#component-scope)

State defined in a `.wire` file is **scoped to the component instance**.

* If a user opens the page, a new instance of the component (and its state) is created.
* The state persists for the lifetime of that user’s connection.
* If the user refreshes the page, the state resets (unless you implement external persistence like a database).

### Shared State

[Section titled “Shared State”](#shared-state)

To share state between components or users, you should use standard Python patterns:

* **Global Variables**: Define `wire()` objects in a separate `.py` module and import them. This creates global, singleton state shared by *all* users (be careful!).
* **Databases/Sessions**: For user-specific persistent data, save to a database and load it into `wire()` variables during the `mount()` lifecycle hook.

# The .wire File

> Understanding the PyWire component file format.

PyWire components are defined in `.wire` files. These files combine Python logic and HTML templates in a single file, separating them with a triple-dash (`---html---`) marker.

## Structure

[Section titled “Structure”](#structure)

A `.wire` file typically has two parts:

1. **Python Block**: (Top) Define your reactive state, imports, and event handlers.
2. **HTML Block**: (Bottom) Define the UI using standard HTML and PyWire template syntax.

```pywire
# Python Block
name = wire("World")


---html---
<!-- HTML Block -->
<h1>Hello, {name.value}</h1>
```

## Compilation

[Section titled “Compilation”](#compilation)

When you run your app, PyWire compiles these files into standard Python classes. This means you get full IDE support for the Python block, and the framework can optimize the rendering process.

The HTML block supports:

* **Interpolation**: `{variable.value}`
* **Attributes**: `attr={value}` or `{attr}`
* **Events**: `@click={handler}`
* **Control Flow**: `$if`, `$for`

# App Initialization

> Configuring and starting the PyWire application.

Every PyWire project starts with an application instance. This is typically defined in a file named `app.py` or `main.py` in your project root.

## The `PyWire` Class

[Section titled “The PyWire Class”](#the-pywire-class)

The `PyWire` class is the main entry point. It initializes the ASGI application, the router, and the compilation engine.

main.py

```python
from pywire import PyWire


app = PyWire()
```

### Configuration Options

[Section titled “Configuration Options”](#configuration-options)

You can customize the application behavior by passing arguments to the constructor:

```python
app = PyWire(
    # Directory (relative to project root) containing your .wire pages (default: "pages")
    pages_dir="src/pages",


    # Enable file-system based routing (default: True)
    path_based_routing=True,


    # Enable PJAX (smooth page transitions) (default: True)
    enable_pjax=True,


    # Enable debug mode (exposes source maps, etc.) (default: False)
    debug=True,


    # Directory (relative to project root) containing your static assets (default: "/static")
    static_path="/assets"
)
```

## Running the App

[Section titled “Running the App”](#running-the-app)

### Development

[Section titled “Development”](#development)

When you run `pywire dev`, the CLI automatically looks for a module exposing an `app` variable that is an instance of `PyWire`.

```sh
# Auto-discovery
pywire dev


# Explicit pointer
pywire dev src.main:app


# No TUI
pywire dev --no-tui
```

### Production

[Section titled “Production”](#production)

For production, you use `pywire run`, which wraps Uvicorn.

```sh
pywire run src.main:app --workers 4
```

## Serving Static Files

[Section titled “Serving Static Files”](#serving-static-files)

If you have a `static/` directory in your project root, PyWire will automatically serve files from it at the `/static` URL prefix.

Example structure:

```text
project/
├── static/
│   ├── logo.png
│   └── styles.css
├── pages/
└── main.py
```

You can reference these in your templates:

```html
<img src="/static/logo.png" alt="Logo" />
```

# CLI Reference

> Comprehensive guide to the pywire command-line interface.

The `pywire` CLI is your primary tool for developing, building, and serving applications.

## Global Flags

[Section titled “Global Flags”](#global-flags)

* `--help`: Show help message and exit.
* `--version`: Show the version number.

## `pywire dev`

[Section titled “pywire dev”](#pywire-dev)

Starts the development server.

```sh
pywire dev [APP] [OPTIONS]
```

* **APP**: The application string (e.g., `main:app`). Optional if `main.py` or `app.py` exists.

**Options:**

* `--host TEXT`: Bind host (default: `127.0.0.1`).
* `--port INTEGER`: Bind port (default: `3000`).
* `--ssl-keyfile TEXT`: Path to SSL key file.
* `--ssl-certfile TEXT`: Path to SSL certificate file.
* `--env-file TEXT`: Path to .env file.
* `--no-tui`: Disable the Terminal User Interface and output standard logs.

### The TUI Dashboard

[Section titled “The TUI Dashboard”](#the-tui-dashboard)

Running `dev` opens a rich dashboard:

* **Logs**: View live server logs.

* **Keys**:

  * `l`: Cycle log levels (DEBUG, INFO, ERROR).
  * `y`: Copy logs to clipboard.
  * `r`: Restart server.
  * `q` / `Ctrl+C`: Quit.

## `pywire run`

[Section titled “pywire run”](#pywire-run)

Starts the production server (Uvicorn wrapper). Optimizes for performance and concurrency.

```sh
pywire run [APP] [OPTIONS]
```

**Options:**

* `--host TEXT`: Bind host (default: `0.0.0.0`).
* `--port INTEGER`: Bind port (default: `8000`).
* `--workers INTEGER`: Number of worker processes (default: auto-calculated based on CPU cores).
* `--no-access-log`: Disable access logging for performance.

## `pywire build`

[Section titled “pywire build”](#pywire-build)

Compiles `.wire` files into optimized Python bytecode and generates build artifacts.

```sh
pywire build [APP] [OPTIONS]
```

**Options:**

* `--optimize`: Compile bytecode with optimization (python `-O`).
* `--out-dir TEXT`: Output directory (default: `.pywire/build`).
* `--pages-dir TEXT`: Override pages directory.

## `create-pywire-app`

[Section titled “create-pywire-app”](#create-pywire-app)

(Separate command, typically run via `uvx`) Scaffolds a new project. See [Quickstart](/docs/guides/quickstart).

# Deployment

> Deploying your PyWire application to production.

PyWire applications can be deployed anywhere that supports Python and ASGI (e.g., Fly.io, Railway, DigitalOcean, or your own VPS).

We are still actively working on optimizing the framework for deployment. We aim to support low-cost hobby deployments that frameworks like Astro excel at, but also support major enterprise deployments that require load balancing and where cost and efficiency come into play.

## Preparing for Production

[Section titled “Preparing for Production”](#preparing-for-production)

1. **Build Artifacts**: Run `pywire build` to generate optimized artifacts. *Still WIP*
2. **Environment Variables**: Configure your database connection strings, API keys, etc.
3. **ASGI Server**: Use `pywire run` or a standard ASGI server like Uvicorn or Hypercorn.

```sh
pywire run main:app --host 0.0.0.0 --port 8000
```

## Deployment Options

[Section titled “Deployment Options”](#deployment-options)

Right now we support two deployment options using the `create-pywire-app` quickstart.

### Docker

[Section titled “Docker”](#docker)

We recommend using Docker for easy and portable deployment. The generated Docker image installs only the modules needed to keep the image small and the build fast.

### Fly.io

[Section titled “Fly.io”](#flyio)

We offer a pre-configured [Fly.io](https://fly.io/) deployment template to get your app from development to production faster and with less headache.

# Editor Setup

> Configuring your editor for PyWire development.

PyWire provides first-class support for VS Code through our official extension.

## VS Code Extension

[Section titled “VS Code Extension”](#vs-code-extension)

[Install to VS Code](vscode:extension/pywire.pywire) | [Visual Studio Marketplace](https://marketplace.visualstudio.com/items?itemName=pywire.pywire)

The PyWire extension provides:

* Syntax highlighting for `.wire` files.
* IntelliSense for the Python block.
* Real-time error reporting.
* Go to definition and hover support.

To install:

1. Open VS Code.
2. Go to the Extensions view (`Ctrl+Shift+X`).
3. Search for “PyWire”.
4. Click **Install**.

## Other Editors

[Section titled “Other Editors”](#other-editors)

Right now we only offer VS Code first-class support for editor extensions. While this may change down the line with demand, it is not currently in the roadmap. Creating integrations for other editors like [Neovim](https://neovim.io) and [Zed](https://zed.dev) should be relatively easy due to the official [Language Server](https://github.com/pywire/pywire-language-server), [Tree Sitter Grammar](https://github.com/pywire/tree-sitter-pywire), and [Prettier Plugin](https://github.com/pywire/prettier-plugin-pywire).

# Forms & Validation

> Handling user input and validation cleanly.

PyWire provides a powerful, schema-less approach to form validation that leverages standard HTML attributes and Python logic.

## Automatic Validation Schema

[Section titled “Automatic Validation Schema”](#automatic-validation-schema)

When you use the `@submit` event on a `<form>`, PyWire automatically scans the form’s input fields (`required`, `min`, `max`, `pattern`, `type`) and builds a validation schema on the server.

You don’t need to define a Pydantic model manually (though you can). The HTML *is* the schema.

```pywire
errors = wire({})


def handle_submit(data):
    # data is a dictionary of the form inputs
    print("Form valid:", data)


---html---
<form @submit={handle_submit}>
    <div>
        <label>Username</label>
        <input name="username" required minlength="3">
        <span class="error" $if={errors.get('username')}>
            {errors.get('username')}
        </span>
    </div>


    <div>
        <label>Age</label>
        <input name="age" type="number" min="18">
        <span class="error" $if={errors.get('age')}>
            {errors.get('age')}
        </span>
    </div>


    <button type="submit">Register</button>
</form>
```

### How it Works

[Section titled “How it Works”](#how-it-works)

1. **Extraction**: The compiler sees `@submit`. It parses all child `<input>` tags.

2. **Rules**: It sees `name="username" required`. It adds a rule: `username` must be present.

3. **Execution**: When the form submits, PyWire intercepts the event.

4. **Validation**: Before calling `handle_submit`, PyWire validates the incoming data against the extracted rules.

5. **Routing**:

   * **Valid**: Calls `handle_submit(data)`.
   * **Invalid**: Intercepted before calling `handle_submit` and populates `errors` dict.

## Reactive Validation Attributes

[Section titled “Reactive Validation Attributes”](#reactive-validation-attributes)

You can bind validation attributes dynamically.

```html
<!-- Field is required only if 'is_company' checkbox is checked -->
<input name="company_name" required="{is_company.value}" />
```

# Introduction

> What is PyWire and why should you use it?

**PyWire** is a “Live Conduit” framework for building modern, reactive web applications using only Python. It bridges the gap between server-side logic and client-side interactivity without requiring you to write a single line of JavaScript.

## The Philosophy

[Section titled “The Philosophy”](#the-philosophy)

Modern web development often requires maintaining two separate codebases: a backend API (Python, Go, Node) and a frontend SPA (React, Vue, Svelte). This adds complexity, duplicates logic (validation, types), and introduces synchronization headaches.

PyWire takes a different approach: **HTML-over-the-wire**.

1. **State Lives on the Server**: All application state is maintained in Python processes on the server.
2. **Logic is Python**: Event handlers, validation, and business logic are written in standard Python.
3. **The “Wire” Updates the View**: When state changes, PyWire calculates the minimal DOM updates required and sends them over a persistent WebSocket connection to the browser.

## Key Features

[Section titled “Key Features”](#key-features)

### 🐍 Python-First Reactivity

[Section titled “🐍 Python-First Reactivity”](#-python-first-reactivity)

Define reactive variables using `wire()`. When you update them in your Python code, the UI updates automatically.

```python
count = wire(0)


def increment():
    $count += 1
```

### ⚡ No JavaScript Required

[Section titled “⚡ No JavaScript Required”](#-no-javascript-required)

You write HTML templates and Python logic. The framework handles the client-side interactivity, event listeners, and DOM manipulation.

### 📂 File-System Routing

[Section titled “📂 File-System Routing”](#-file-system-routing)

Create files in the `pages/` directory to automatically define routes, supporting dynamic parameters like `pages/users/[id].wire`.

### 🛠️ Developer Experience

[Section titled “🛠️ Developer Experience”](#️-developer-experience)

Includes a robust CLI with a Terminal User Interface (TUI) for real-time logs, hot-reloading, and debugging tools.

## How it Works

[Section titled “How it Works”](#how-it-works)

A PyWire application consists of `.wire` files. These files are compiled into Python classes that handle:

* **Rendering**: Generating the initial HTML.
* **Hydration**: Establishing a WebSocket connection.
* **Events**: Receiving events (clicks, inputs) from the browser.
* **Updates**: Sending precise DOM patches back to the client.

Ready to see it in action? Let’s [build your first component](/docs/guides/your-first-component).

# Layouts

> Reusing UI structures with layouts.

Layouts allow you to wrap multiple pages in a consistent UI structure (like headers, footers, and sidebars).

## Creating a Layout

[Section titled “Creating a Layout”](#creating-a-layout)

A layout is just an ordinary `.wire` file that uses the `<slot />` tag to indicate where page content should be injected.

```html
<nav>
  <a href="/">Home</a>
  <a href="/about">About</a>
</nav>


<main>
  <slot />
</main>


<footer>© 2026 PyWire</footer>
```

## Using a Layout

[Section titled “Using a Layout”](#using-a-layout)

Using a layout depends on whether your project uses path-based routing (default) or explicit routing.

### Layouts in Path-based Routing

[Section titled “Layouts in Path-based Routing”](#layouts-in-path-based-routing)

The layout system functions similar to Svelte in this way—via hierarchy. You create your layout with the name `__layout__.wire` in the path where it should apply. For example, if you created a layout in the root of the pages directory, `src/pages/`, it would apply to all pages automatically

### Layouts in Explicit Routing

[Section titled “Layouts in Explicit Routing”](#layouts-in-explicit-routing)

Since file path and hierarchy do not determine routing in projects using explicit routing, you can give your layout any name and put it in any file path. You can use a layout on a `.wire` page with the `!layout` directive.

```pywire
!path "/my-page"
!layout "path/to/layout.wire"
```

# Quickstart

> Get up and running with PyWire in seconds.

Welcome to PyWire! This guide will help you set up your first project instantly using our scaffolding tools.

## The Fastest Way: `create-pywire-app`

[Section titled “The Fastest Way: create-pywire-app”](#the-fastest-way-create-pywire-app)

The easiest way to start a new project is using `uvx` to run our interactive scaffolding tool.

```sh
uvx create-pywire-app
```

This command will launch an interactive wizard that guides you through:

1. **Project Name**: Naming your new application.
2. **Template Selection**: Choosing a starter template (e.g., Counter, Blog, SaaS Starter).
3. **Routing Style**: Selecting between file-system based routing (like Svelte) or explicit routing (more like Flask/FastAPI).
4. **Configuration**: Setting up Git, VS Code extensions, and more.

Once the setup is complete, navigate into your new project directory:

```sh
cd my-pywire-app
```

## Installation Scripts

[Section titled “Installation Scripts”](#installation-scripts)

If you don’t have `uv` installed yet, you can use our automated installation scripts to set up everything for you.

### macOS / Linux

[Section titled “macOS / Linux”](#macos--linux)

```sh
curl -fsSL pywire.dev/install | sh
```

### Windows (PowerShell)

[Section titled “Windows (PowerShell)”](#windows-powershell)

```powershell
irm pywire.dev/install.ps1 | iex
```

## Running the Development Server

[Section titled “Running the Development Server”](#running-the-development-server)

To start your application in development mode, use the `pywire dev` command. This starts a high-performance server with hot-reloading and a live TUI dashboard.

```sh
pywire dev
```

Your app will be available at `http://localhost:3000`.

## What’s Next?

[Section titled “What’s Next?”](#whats-next)

* Check out the [Introduction](/docs/guides/introduction) to understand the core philosophy.
* Build your first component in the [Walkthrough](/docs/guides/your-first-component).

# Routing

> Defining routes in PyWire.

PyWire supports both file-system based routing and explicit routing.

## File-System Routing

[Section titled “File-System Routing”](#file-system-routing)

By default, PyWire looks in the `pages/` directory and automatically creates routes based on the file structure.

* `pages/index.wire` -> `/`
* `pages/about.wire` -> `/about`
* `pages/contact/index.wire` -> `/contact`

### Dynamic Routes

[Section titled “Dynamic Routes”](#dynamic-routes)

Use square brackets to define dynamic parameters.

* `pages/posts/[slug].wire` -> `/posts/my-first-post` (accessible via `slug` variable on the page)
* `pages/users/[uid]/profile.wire` -> `/users/42/profile` (accessible via `uid` variable on the page)

## Explicit Routing

[Section titled “Explicit Routing”](#explicit-routing)

You can also define routes explicitly. First, set `path_based_routing` (default True) to False in your PyWire app init.

```python
from pywire import PyWire


app = PyWire(path_based_routing=False)
```

Then, add `!path` declarations to your pages.

```pywire
# A single route matching path
!path "/home"


<section>
    <h1>Home</h1>
</section>
```

You can match multiple routes, handle URL parameters, and automatically create SPA-like apps but with deep linking.

```pywire
# A single pages matching multiple paths
!path { "/home": "home", "/user/:uid": "user" }


<!-- Conditionally render based on route matched -->
<section>
    <h1 $if={path.home}>Home</h1>
    <h1 $if={path.user}>User {params.uid}</h1>
</section>
```

## Navigation

[Section titled “Navigation”](#navigation)

Standard `<a>` tags work out of the box. If `enable_pjax=True` (default), PyWire intercepts clicks on internal links and performs a “soft navigation” via `fetch` + HTML replacement, avoiding a full page reload.

```html
<a href="/about">About Us</a>
```

# Your First Component

> Build a reactive counter component in PyWire.

Building a component in PyWire is as simple as writing HTML and adding a bit of Python for logic.

Let’s look at a classic counter example.

```pywire
count = wire(0)


def increment():
    $count += 1


---html---
<button @click={increment}>
    Increment
</button>


<h1>Current Count: {count.value}</h1>


<div $if={count.value > 10}>
    Wow, you're clicking fast!
</div>
```

## Adding More Interactivity

[Section titled “Adding More Interactivity”](#adding-more-interactivity)

You can use standard HTML attributes and even add conditional styling.

```html
count = wire(0) def increment(): $count += 1 ---html---
<h1>Count: {count.value}</h1>


<button @click="{increment}" $disabled="{count.value">= 10}> Increment (Max 10)</button>


<p $show="{count.value">5} style="color: red;"> High count alert!</p>
```

In the next sections, we’ll dive deeper into the `.wire` file format and how reactivity works.

# Core API Reference

This reference documents the core Python API for PyWire. It covers the essential primitives for state management, application configuration, and runtime interaction.

## Core Primitives

[Section titled “Core Primitives”](#core-primitives)

***

### `wire`

[Section titled “wire”](#wire)

The fundamental building block of reactive state in PyWire.

```py
class wire(initial_value: Any, **kwargs: Any)
```

**Description:** Wraps a value to make it reactive. When the value changes, any component rendering this wire is automatically scheduled for an update.

**Arguments:**

* **`initial_value`** (`Any`): The starting value. This can be a primitive (int, str, bool), a list, a dictionary, or an object.

* **`**kwargs`** (`Any`): If provided, the wire is initialized as a **Namespace** object (similar to a dictionary or `SimpleNamespace`), where keys become reactive attributes.

**Properties:**

* **`.value`**: Accesses or modifies the underlying value. Writing to this property triggers reactivity.

**Usage:**

```py
from pywire import wire


# 1. Primitive State
count = wire(0)
print(count.value)  # Read
count.value += 1    # Write (Trigger)


# 2. Namespace State (Object-like)
user = wire(name="Alice", age=30)
print(user.name)    # Read attribute
user.age = 31       # Write attribute (Trigger)
```

**Note:** Inside a `.wire` file’s Python block, you can use the `$` prefix sugar (e.g., `$count`, `$user.age`) which compiles to `.value`.

## Application Class

[Section titled “Application Class”](#application-class)

***

### `PyWire`

[Section titled “PyWire”](#pywire)

The main ASGI application entry point.

```py
class PyWire(
    pages_dir: str = "pages",
    path_based_routing: bool = True,
    enable_pjax: bool = True,
    debug: bool = False,
    static_path: str = "/static"
)
```

**Description:** Initializes the PyWire runtime, setting up the router, compiler, and WebSocket server. It conforms to the ASGI specification.

**Parameters:**

* **`pages_dir`** (`str`): Path to the directory containing your `.wire` files relative to the application root. Defaults to `"pages"`.

* **`path_based_routing`** (`bool`): If `True`, automatically generates routes based on the file structure in `pages_dir`. Defaults to `True`.

* **`enable_pjax`** (`bool`): If `True`, intercepts internal link clicks to perform soft navigations (HTML replacement) instead of full page reloads. Defaults to `True`.

* **`debug`** (`bool`): Enables developer tools, including the TUI dashboard, source maps, and detailed error overlays. Defaults to `False`.

* **`static_path`** (`str`): The URL prefix for serving static files. Defaults to `"/static"`.

**Example:**

```py
from pywire import PyWire


app = PyWire(pages_dir="src/pages", debug=True)
```

## Lifecycle Hooks

[Section titled “Lifecycle Hooks”](#lifecycle-hooks)

***

These functions are optional definitions you can place inside your component’s script block.

### `mount`

[Section titled “mount”](#mount)

**Description:** Runs **once** on the server when the component is first initialized for a user session. This is the ideal place to load data, check authentication, or initialize `wire` variables based on URL parameters.

**Example:**

pages/users/\[id].wire

```py
user_id = wire(None)
user_data = wire({})


@mount
def fetch_data(params):
    $user_id = params.get("id")
    # Fetch data from database synchronously or asynchronously
    $user_data = db.get_user($user_id)
```

## Runtime Helpers

[Section titled “Runtime Helpers”](#runtime-helpers)

***

Utility functions available in the `pywire.runtime.helpers` module to interact with the client-side environment from the server.

### `relocate`

[Section titled “relocate”](#relocate)

```py
def relocate(path: str) -> None
```

**Description:** Commands the browser to navigate to a new URL. This is handled via the WebSocket connection.

**Arguments:**

* **`path`** (`str`): The destination URL (relative or absolute).

**Example:**

```py
from pywire.runtime.helpers import relocate


def login_handler():
    if verify_user():
        relocate("/dashboard")
```

## Template Context Variables

[Section titled “Template Context Variables”](#template-context-variables)

***

Special variables available strictly within the HTML template context.

### `$event`

[Section titled “$event”](#event)

Represents the client-side DOM event payload. Available **only** inside event handler expressions (e.g., `@click={...}`).

**Properties:**

* **`.value`** (`Any`): The `value` property of the target element.

  * For `<input type="text">`, returns the string text.

  * For `<input type="checkbox">`, returns `True` or `False`.

  * For `<select>`, returns the selected option’s value.

* **`.key`** (`str`): The key value for keyboard events (e.g., `"Enter"`, `"Escape"`, `"a"`).

* **`.target`** (`dict`): A dictionary containing serialized attributes of the DOM element that triggered the event (id, class, name, dataset, etc.).

**Example:**

```html
<!-- Accessing input value -->
<input @input="{update_text($event.value)}" />


<!-- Accessing specific key press -->
<input @keydown="{handle_key($event.key)}" />
```

# Control Flow Blocks

> Rendering logic using {$if}, {$for}, {$await}, and {$try} blocks.

PyWire provides a structured block syntax to handle dynamic rendering logic directly in your HTML. These blocks allow you to condition, loop, wait, and catch errors without writing complex Python logic inside your elements.

## Syntax Overview

[Section titled “Syntax Overview”](#syntax-overview)

***

All blocks follow a consistent pattern using the brace-dollar sigil `{$...}`.

* **Opener:**`{$keyword expression}` (e.g., `{$if user.is_admin}`)

* **Branches:**`{$keyword}` (e.g., `{$else}`)

* **Closer:**`{/keyword}` (e.g., `{/if}`)

## Conditionals (`{$if}`)

[Section titled “Conditionals ({$if})”](#conditionals-if)

***

The `{$if}` block renders content based on the truthiness of a Python expression. It supports `elif` and `else` branches.

### Syntax

[Section titled “Syntax”](#syntax)

```pywire
{$if condition}
    <!-- Rendered if condition is Truthy -->
{$elif other_condition}
    <!-- Rendered if first condition is False and this is Truthy -->
{$else}
    <!-- Rendered if all above are False -->
{/if}
```

### Examples

[Section titled “Examples”](#examples)

**Basic Visibility:**

```pywire
{$if is_logged_in}
    <UserProfile user={user} />
{$else}
    <LoginButton />
{/if}
```

**Complex Logic:** You can use standard Python operators (`and`, `or`, `not`, `in`) inside the block.

```pywire
{$if user.role == "admin" and len(notifications) > 0}
    <AdminAlerts />
{/if}
```

## Loops (`{$for}`)

[Section titled “Loops ({$for})”](#loops-for)

***

The `{$for}` block iterates over any Python iterable (list, tuple, dictionary, generator).

### Syntax

[Section titled “Syntax”](#syntax-1)

```pywire
{$for target in iterable, key=unique_id}
    <!-- Rendered for each item -->
{$else}
    <!-- Rendered if the iterable is empty -->
{/for}
```

### The `key` Argument

[Section titled “The key Argument”](#the-key-argument)

Providing a `key` is **strongly recommended**. It allows PyWire to track identity across re-renders, ensuring that state (like focus or input text) is preserved when the list order changes.

* **Syntax:**`key=<expression>` (comma separated from the loop).

### Examples

[Section titled “Examples”](#examples-1)

**List Iteration:**

```pywire
<ul>
    {$for todo in todos, key=todo.id}
        <li class={todo.status}>
            {todo.text}
        </li>
    {$else}
        <li>No todos yet!</li>
    {/for}
</ul>
```

**Dictionary Iteration:**

```pywire
<dl>
    {$for key, value in config.items(), key=key}
        <dt>{key}</dt>
        <dd>{value}</dd>
    {/for}
</dl>
```

## Async Data (`{$await}`)

[Section titled “Async Data ({$await})”](#async-data-await)

***

The `{$await}` block handles Python **Awaitables** (coroutines, Tasks, Futures). It manages the three states of an async operation: **Pending**, **Resolved**, and **Rejected**.

### Syntax

[Section titled “Syntax”](#syntax-2)

```pywire
{$await awaitable_expression}
    <!-- 1. PENDING: Rendered immediately while waiting -->
{$then result_name}
    <!-- 2. RESOLVED: Rendered when the task finishes -->
{$catch error_name}
    <!-- 3. REJECTED: Rendered if an exception is raised -->
{/await}
```

### Examples

[Section titled “Examples”](#examples-2)

**Fetching Data:**

```pywire
{$await db.get_user(user_id)}
    <div class="skeleton">Loading profile...</div>


{$then user}
    <h1>{user.name}</h1>
    <p>{user.bio}</p>


{$catch e}
    <div class="error">
        Could not load user: {str(e)}
    </div>
{/await}
```

**Fire-and-Forget:** You can omit the variable names if you don’t need the result value.

```pywire
{$await log_view_event()}
    <!-- No pending UI needed -->
{$then}
    <small>View logged.</small>
{/await}
```

## Error Boundaries (`{$try}`)

[Section titled “Error Boundaries ({$try})”](#error-boundaries-try)

***

The `{$try}` block creates a safety zone. If an exception occurs while rendering the content inside (including inside child components), the `{$except}` block is rendered instead of crashing the page.

### Syntax

[Section titled “Syntax”](#syntax-3)

```pywire
{$try}
    <!-- Safe Zone -->
{$except ExceptionType as e}
    <!-- Error Handler -->
{$else}
    <!-- Optional: Runs if no error -->
{$finally}
    <!-- Optional: Runs always -->
{/try}
```

### Examples

[Section titled “Examples”](#examples-3)

**Unsafe User Content:** Useful when rendering content that might fail validation or parsing.

```pywire
{$try}
    {$html render_markdown(user_bio)}
{$except ValueError}
    <p class="warning">Invalid markdown formatting.</p>
{$except Exception}
    <p class="error">Unknown error rendering bio.</p>
{/try}
```

# Control Flow ($if, $for)

> Conditional rendering and loops in PyWire templates.

PyWire provides special attributes for controlling the structure of your HTML.

## Conditional Rendering (`$if`)

[Section titled “Conditional Rendering ($if)”](#conditional-rendering-if)

Use `$if` to conditionally include an element in the DOM.

```pywire
user = wire(None)


---html---
<div $if={user.value}>
    Welcome back, {user.name}!
</div>
```

## Loops (`$for`)

[Section titled “Loops ($for)”](#loops-for)

Use `$for` to render a list of items.

```pywire
items = wire(["Apple", "Banana", "Cherry"])


---html---
<ul>
    <li $for={item in items.value}>
        {item}
    </li>
    <li $if={len(items) == 0}>
        No items found.
    </li>
</ul>
```

## Visibility (`$show`)

[Section titled “Visibility ($show)”](#visibility-show)

Unlike `$if`, which adds or removes elements from the DOM, `$show` toggles the `display: none` CSS property. Use this for elements that need to toggle frequently without full DOM reconstruction.

```pywire
is_visible = wire(False)


---html---
<div $show={is_visible.value}>
    I'm hidden but still in the DOM!
</div>
```

# Event Modifiers

> Fine-tuning event behavior with modifiers.

PyWire supports several event modifiers to simplify common tasks like preventing default behavior or debouncing inputs.

## Common Modifiers

[Section titled “Common Modifiers”](#common-modifiers)

* `.prevent`: Calls `event.preventDefault()`.
* `.stop`: Calls `event.stopPropagation()`.
* `.enter`: Only triggers if the “Enter” key was pressed.
* `.outside`: Triggers when a click occurs outside the element.

```html
<form @submit.prevent="{handle_submit}">
  <input @keydown.enter="{add_item}" />
  <button>Submit</button>
</form>


<div class="modal" @click.outside="{close_modal}">Modal Content</div>
```

## Input Modifiers

[Section titled “Input Modifiers”](#input-modifiers)

* `.debounce.ms`: Delays the event handler until a specified number of milliseconds have passed since the last event.
* `.throttle.ms`: Ensures the event handler is called at most once every specified number of milliseconds.

```html
<input type="text" @input.debounce.300="{search_users}" />
```

## Error Handling

[Section titled “Error Handling”](#error-handling)

The `.error` modifier allows you to catch validation errors or server-side exceptions for a specific event.

```html
<form @submit="{save_data}" @submit.error="{handle_error}">...</form>
```

# Interpolation & Attributes

> Binding data to your HTML templates.

PyWire templates use a simple syntax for embedding Python values and binding attributes.

## Interpolation

[Section titled “Interpolation”](#interpolation)

Use curly braces `{}` to embed Python expressions directly into your HTML.

```pywire
user = wire(name="Alice")


---html---
<h1>Hello, {user.name}</h1>
<p>The result is {10 * 5}</p>
<p>Status: {get_status_message()}</p>
```

## Attribute Binding

[Section titled “Attribute Binding”](#attribute-binding)

There are two ways to bind attributes dynamically:

### Reactive Attributes

[Section titled “Reactive Attributes”](#reactive-attributes)

Use brackets instead of quotes to bind an attribute to a Python expression. It follows the same reactivity rules as interpolation.

```pywire
is_active = wire(True)
theme_color = wire("blue")


---html---
<div class={{'active': $is_active}}"
     style={f"color: {theme_color.value}"}>
    Dynamic content
</div>
```

# Welcome to PyWire

> Welcome to PyWire! This tutorial will guide you through the basics of building reactive web applications.

Welcome to the **PyWire Interactive Tutorial**!

PyWire is a pythonic framework for building reactive web interfaces with minimal boilerplate. In this tutorial, you’ll learn the core concepts by building real examples directly in your browser.

This first step is an introduction. You don’t need to write any code yet. Take a moment to look at the project structure on the left and the preview on the right. When you’re ready, click the **Next** button to continue.

# Your first page

> Build your first reactive page by modifying HTML and adding styles.

Let’s start by modifying the HTML of your first PyWire page.

### Your Task

[Section titled “Your Task”](#your-task)

1. Inside `index.wire`, change the text inside the `<h1>` tag from “PyWire” to **“Hello PyWire!”**.
2. Add a `<strong>` tag with the text “Success!” below the paragraph.

Notice how the preview updates instantly as you make changes. The checklist on the left will track your progress!

# Interpolation

> Use curly braces to embed Python expressions directly into your HTML.

In PyWire, you can embed any Python expression inside your HTML by wrapping it in curly braces `{}`.

### Your Task

[Section titled “Your Task”](#your-task)

1. Replace the static “0” in the `<p>` tag with **`{count}`**.
2. Once you’ve done that, click the **Increment** button in the preview 3 times until the text shows “The count is: 3”.

PyWire automatically tracks dependencies, so whenever `count` changes, the UI updates instantly!

# Dynamic attributes

> Bind attributes to Python expressions using curly braces.

Just like content interpolation, you can use curly braces to make HTML attributes dynamic.

### Your Task

[Section titled “Your Task”](#your-task)

1. Update the `<img>` tag to use the `src` and `alt` variables. You can use the shorthand syntax: `<img {src} {alt} />`.
2. Verify that the PyWire logo appears in the preview.

If the attribute name and the variable name are the same, `{src}` is equivalent to `src={src}`.

# Styling

> Learn how to use scoped CSS in your PyWire components.

PyWire supports scoped styling via the `<style scoped>` tag. Styles defined here only apply to elements within this file.

### Your Task

[Section titled “Your Task”](#your-task)

1. Inside the `<style scoped>` block, set the color of the `.title` class to `#22d3ee`.
2. Set the color of all `<p>` tags to `#94a3b8`.

Notice how these styles don’t leak out to other components (if we had any), and global styles don’t easily override them!

# Escaping HTML

> Render raw HTML strings safely using the $html directive.

By default, PyWire escapes all interpolated values to prevent XSS attacks. If you have trust-worthy HTML that you want to render as-is, use the `{$html ...}` directive.

### Your Task

[Section titled “Your Task”](#your-task)

1. Change `{content}` to **`{$html content}`** inside the `<div>`.
2. Observe how the raw text transforms into formatted HTML (Bold and Italic).

**Caution**: Never use `{$html ...}` with untrusted user input!

# The wire primitive

> Create reactive state with wire() and mutate it with the $ prefix.

Reactivity in PyWire centers around the `wire()` primitive and the `$` shorthand for mutation.

### Your Task

[Section titled “Your Task”](#your-task)

1. Initialize a reactive variable named `count` with a value of `0` using `wire(0)`.
2. Inside the `increment` function, use the magic **`$count`** syntax to add 1 to the count.
3. Click the button until the count reaches **5**.

In PyWire, whenever you use `$name = value` or `$name += value`, it doesn’t just change the local variable – it updates the reactive state and triggers a UI patch!

# Wire as a namespace

> Use wire() to manage complex state objects as namespaces.

The `wire()` function can take a dictionary or object, creating a reactive namespace. You can access and mutate nested properties using the same `$` shorthand.

### Your Task

[Section titled “Your Task”](#your-task)

1. In the `track_click` function, increment `user.clicks` using the **`$user.clicks`** syntax.
2. Click the button 3 times.

Using `wire()` for objects lets you group related state together while keeping everything reactive.

# Event handlers

> Listen for browser events using the @ prefix.

In PyWire, event listeners are added using the `@` prefix, followed by the event name (like `@click`, `@input`, `@submit`).

### Your Task

[Section titled “Your Task”](#your-task)

1. Add `@click={increment}` to the `<button>` tag.
2. Test it by clicking the button 3 times in the preview.

Events in PyWire automatically prevent default behavior if they are on a form submission, but otherwise behave like standard DOM events.

# Expressions vs Functions

> Use inline Python expressions or function names as event handlers.

Event handlers in PyWire can be either a reference to a function, a function call, or a raw Python expression.

### Your Task

[Section titled “Your Task”](#your-task)

1. The first button already uses an inline expression: `@click={$count += 1}`.
2. Add `@click={reset()}` to the second button to call the `reset` function.
3. Increment the count, then verify that the Reset button works.

Inline expressions are great for simple updates, while functions are better for complex logic.

# Event modifiers

> Use modifiers to change event behavior, like @click.once.

PyWire supports event modifiers to handle common patterns without writing extra boilerplate. Modifiers are added after the event name with a dot.

### Your Task

[Section titled “Your Task”](#your-task)

1. Add `@click.once={$count += 1}` to the “Click Only Once” button.
2. Click that button multiple times and notice that the count only increments once.

Other common modifiers include `.prevent` (to prevent default), `.stop` (to stop propagation), and `.enter` (for keyup events).

# Conditionals

> Learn how to conditionally render elements using {$if}.

PyWire uses `{$if}` blocks to handle conditional rendering. Unlike CSS toggles (which hide elements but keep them in the DOM), `{$if}` blocks physically add or remove elements from the document structure based on the condition.

### Your Task

[Section titled “Your Task”](#your-task)

1. The `is_visible` state toggles between `True` and `False` when the button is clicked.
2. Wrap the `.alert` div in an `{$if is_visible} ... {/if}` block so it is hidden by default.
3. Click the button to reveal it.

#### Examples

[Section titled “Examples”](#examples)

**Basic Visibility:**

```pywire
{$if is_visible}
    <div class="alert">
        Secret message revealed!
    </div>
{/if}
```

**With Else:**

```pywire
{$if is_logged_in}
    <UserProfile />
{$else}
    <LoginButton />
{/if}
```

# Loops

> Render lists of data using {$for}.

To render lists, use the `{$for}` block. It works just like a Python `for` loop.

Crucially, you should provide a `key` argument (separated by a comma). This helps PyWire track items efficiently when the list order changes.

### Your Task

[Section titled “Your Task”](#your-task)

1. Inside the `<ul>`, create a `{$for}` block to iterate over `todos`.
2. Use `item in todos` as the loop expression.
3. Use `key=item['id']` for the unique key.
4. Render the `item['text']` inside a `<li>`.

#### Examples

[Section titled “Examples”](#examples)

**Basic Loop:**

```pywire
<ul>
    {$for user in users, key=user.id}
        <li>{user.name}</li>
    {/for}
</ul>
```

**With Else (Empty State):**

```pywire
<ul>
    {$for item in items, key=item.id}
        <li>{item.name}</li>
    {$else}
        <li>No items found.</li>
    {/for}
</ul>
```

# Async Data

> Handle loading states with {$await}.

PyWire makes working with asynchronous data easy. Instead of managing `is_loading` variables manually, you can use the `{$await}` block to handle Python coroutines directly in the template.

The block immediately renders the first section (Pending state), and automatically updates to the `{$then}` section when the data resolves.

### Your Task

[Section titled “Your Task”](#your-task)

1. Call the `fetch_user_data()` function inside an `{$await}` block.
2. Show `<p>Loading user...</p>` as the pending state.
3. Add a `{$then name}` block to capture the result and display `Welcome, {name}!`.

#### Examples

[Section titled “Examples”](#examples)

**Fetching Data:**

```pywire
{$await api.get_profile(user_id)}
    <Spinner />
{$then profile}
    <ProfileCard user={profile} />
{$catch error}
    <p>Error: {error}</p>
{/await}
```

# Error Boundaries

> Learn how to handle exceptions gracefully using {$try}.

Errors happen—APIs fail, inputs are invalid, or calculations go wrong. In PyWire, if an exception is raised during rendering, it can prevent the entire component (or page) from displaying.

The `{$try}` block creates a **safety zone**. If an error occurs inside it, PyWire catches the exception and renders the `{$except}` block instead.

### Your Task

[Section titled “Your Task”](#your-task)

1. The `get_data()` function has a 50% chance of raising a `ValueError`.
2. Currently, if it fails, the preview might crash or show a generic error.
3. Wrap the `<p>` tag calling `get_data()` inside a `{$try} ... {/try}` block.
4. Add an `{$except ValueError as e}` block to display the error message nicely (you can use `str(e)` to get the message).

#### Examples

[Section titled “Examples”](#examples)

**Basic Error Handling:**

```pywire
{$try}
    <p>Result: {risky_calculation()}</p>
{$except ValueError}
    <p>Calculation failed.</p>
{/try}
```

**Accessing the Exception:**

```pywire
{$try}
    {perform_critical_task()}
{$except Exception as e}
    <div class="error-banner">
        System Error: {str(e)}
    </div>
{/try}
```

# Conditional logic ($if)

> Use the $if attribute to conditionally render elements.

PyWire provides several “framework attributes” that start with `$`. The `$if` attribute controls whether an element is even present in the DOM.

### Your Task

[Section titled “Your Task”](#your-task)

1. Add `$if={show}` to the `<div>` containing the “hidden message”.
2. The message should disappear.
3. Click the button to reveal it.

Unlike hiding with CSS, `$if` completely adds or removes the element from the document.

# Visibility ($show)

> Use the $show attribute to toggle visibility with CSS (display: none).

The `$show` attribute toggles an element’s visibility using the CSS `display` property. This is useful when you want to keep the element in the DOM (e.g., for transitions or maintaining focus) but hide it from view.

### Your Task

[Section titled “Your Task”](#your-task)

1. Add `$show={visible}` to the message `<div>`.
2. Toggle the visibility using the button.

Compare this to `$if` from the previous step – visually they look similar, but under the hood `$show` just applies `display: none`.

# Loops ($for)

> Use the $for attribute to render lists of elements.

The `$for` attribute allows you to repeat an element for each item in a list. It uses Python’s standard `for ... in ...` syntax.

### Your Task

[Section titled “Your Task”](#your-task)

1. Add `$for={item in items}` to the `<li>` tag.
2. Use `{item}` inside the `<li>` to display the fruit name.
3. Click the “Add Date” button and watch the list grow!

For better performance when list items move or change, you can also use `$key` to give each item a unique identity.

# Basic components

> Break your UI into reusable pieces with components.

Components in PyWire are just `.wire` files. Any `.wire` file in your `components/` directory (or other configured paths) can be used as a custom HTML tag.

### Your Task

[Section titled “Your Task”](#your-task)

1. Switch to `components/MyButton.wire` in the file tree.
2. Add a `<style scoped>` block to add a hover effect (e.g. `opacity: 0.8`) to the button.
3. Observe that the button in the preview updates immediately.

In PyWire, directory structure often dictates availability. Files in `components/` are automatically available to your pages.

# Components with props

> Pass data to components using props.

To make components flexible, you can pass data to them using props. Use the `!props` directive at the top of your component file to declare what it accepts.

### Your Task

[Section titled “Your Task”](#your-task)

1. In `components/Badge.wire`, add `!props text, color="gray"` at the very top.
2. Replace “Text here” with **`{text}`**.
3. Check the preview to see the “Admin” and “User” badges rendered with different colors.

Props can have default values, like `color="gray"` in this example.

# Prop spreading

> Spread attributes onto elements for better flexibility.

Sometimes you want a component to accept any arbitrary HTML attributes and apply them to an internal element. This is called “prop spreading”.

### Your Task

[Section titled “Your Task”](#your-task)

1. In `components/CustomInput.wire`, add **`{**attrs}`** to the `<input>` tag.
2. Note how the `placeholder` and `type="password"` from `index.wire` are now correctly applied to the real input element.

The `**attrs` catch-all prop collects all attributes not explicitly named, similar to Python’s `**kwargs`.

# !path

> Override the default routing of a file using the !path directive.

By default, files in the `pages/` directory are served at a route matching their filename. You can override this using the `!path` directive.

### Your Task

[Section titled “Your Task”](#your-task)

1. At the very top of `pages/strange.wire`, add `!path "/home"`.
2. Notice that the preview (which is already pointed at `/home`) now shows the content of this file instead of a 404.

Directives like `!path` allow you to decouple your file structure from your URL structure.

# !layout

> Wrap your pages in a common layout component using !layout.

The `!layout` directive allows you to specify a component that should wrap the current page. The page content is injected wherever the layout component uses the `<slot />` tag.

### Your Task

[Section titled “Your Task”](#your-task)

1. In `pages/index.wire`, add `!layout components/Layout.wire` at the top.
2. Observe how the page is now wrapped in the layout with a header.

Layouts are a powerful way to share common UI elements like navigation bars and footers across multiple pages.

# !component

> Explicitly name a component or register it at a custom tag name.

While PyWire automatically discovers components in certain folders, you can use the `!component` directive to explicitly name a component, which is especially useful for files in deep subdirectories.

### Your Task

[Section titled “Your Task”](#your-task)

1. In `lib/ui/FancyButton.wire`, add `!component MyCustomTag` at the top.
2. Switch back to `pages/index.wire` to see that `<MyCustomTag />` now correctly renders the fancy button.

This gives you full control over how your components are referenced in HTML.

# Explicit routing

> Create single-page applications (SPAs) with ease.

PyWire makes building Single Page Applications (SPAs) effortless. Standard `<a>` tags automatically handle client-side navigation if the target route exists in your PyWire project.

### Your Task

[Section titled “Your Task”](#your-task)

1. In the preview, click the **“Go to About”** link.
2. Once on the About page, click the **“Go Home”** link.

Notice how the navigation is instant – there’s no full browser refresh! This is deep-linking and SPA behavior out of the box.
```
