const express = require('express');
const { Pool } = require('pg');
const app = express();

const pool = new Pool({
  connectionString: "postgres://user:password@db:5432/mydb"
});


app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "*");
  next();
});

app.get('/api/produkty', async (req, res) => {
  try {
    const result = await pool.query('SELECT * FROM produkty');
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.listen(3000, () => console.log('Backend na porcie 3000'));