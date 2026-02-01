# Ancient Water Clock - Setup Tutorial

## What is this?

A 3D ancient water clock (clepsydra) built with Three.js and React. Water fills a cone-shaped funnel, and when you press a button, it drains through the narrow bottom into a bucket — just like the real water clocks used thousands of years ago.

## Prerequisites

You need **Node.js** installed on your computer. If you don't have it:

1. Go to [https://nodejs.org](https://nodejs.org)
2. Download the **LTS** version (the one that says "Recommended")
3. Run the installer and follow the prompts
4. To verify it worked, open a terminal and type:
   ```
   node --version
   ```
   You should see a version number like `v20.x.x`

## Step-by-step Setup

### 1. Open a terminal

- **Mac**: Press `Cmd + Space`, type "Terminal", press Enter
- **Windows**: Press `Win + R`, type "cmd", press Enter
- **Linux**: Press `Ctrl + Alt + T`

### 2. Navigate to the project folder

```
cd path/to/FlowState/frontend
```

Replace `path/to/FlowState` with wherever you saved this project. For example:
```
cd ~/Desktop/FlowState/frontend
```

### 3. Install dependencies

```
npm install
```

This downloads all the libraries the project needs. Wait until it finishes (you'll see your cursor come back).

### 4. Start the app

```
npm run dev
```

You should see output like:
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

### 5. Open it in your browser

Open your web browser (Chrome, Firefox, Safari, Edge) and go to:

```
http://localhost:5173
```

### 6. Use the water clock

- You'll see a 3D cone funnel with water, a bucket below, and a starry background
- **Click and drag** to rotate the camera around the scene
- **Scroll** to zoom in and out
- Press the **"Start Water Flow"** button at the bottom to begin draining
- Watch the water drain from the funnel into the bucket with droplets and caustic light effects
- Press **"Reset"** to stop the draining

### 7. Stop the app

When you're done, go back to the terminal and press `Ctrl + C` to stop the server.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `npm: command not found` | Node.js is not installed. Go back to Prerequisites. |
| `npm install` shows errors | Delete the `node_modules` folder and `package-lock.json`, then run `npm install` again. |
| Blank screen in browser | Open browser developer tools (F12) and check the Console tab for errors. |
| Page won't load | Make sure the terminal still shows the server running. Try `npm run dev` again. |

## Project Files

| File | What it does |
|------|-------------|
| `src/App.jsx` | Main application with camera, lights, UI buttons |
| `src/ConeFunnel.jsx` | The cone-shaped funnel vessel |
| `src/WaterSystem.jsx` | Water surface, caustic lights, droplets, splashes |
| `src/Bucket.jsx` | The bucket that catches water |
| `src/main.jsx` | Entry point that starts the React app |
