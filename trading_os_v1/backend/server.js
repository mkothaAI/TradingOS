// trading-os-v1/backend/server.js
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3001;

app.use(express.json());

// Sample API endpoint
app.get('/api/trading', (req, res) => {
  res.json({
    status: 'success',
    message: 'Trading API is running'
  });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});