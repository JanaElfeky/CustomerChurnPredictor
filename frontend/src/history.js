import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  TextField
} from '@mui/material';
import { getPredictionHistory } from './api';

function PredictionHistory() {
  const [history, setHistory] = useState([]);
  const [limit, setLimit] = useState(20);   // default 20
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadHistory = async (limitValue) => {
    setLoading(true);
    setError('');
    try {
      const data = await getPredictionHistory(limitValue);
      setHistory(data.predictions || []);
    } catch (err) {
      setError(err.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

useEffect(() => {
  // whenever "limit" changes, reload
  loadHistory(limit);
}, [limit]);  // <--- add limit here

const handleLimitChange = (e) => {
  // read the number the user typed
  const raw = e.target.value;
  if (raw === '') {
    setLimit('');           // allow empty while typing
    return;
  }
  const num = Number(raw);
  const clamped = Math.min(50, Math.max(1, isNaN(num) ? 1 : num));
  setLimit(clamped);        // this triggers useEffect -> loadHistory(clamped)
};
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Recent Predictions
      </Typography>

      <TextField
        label="How many predictions?"
        type="number"
        value={limit}
        onChange={handleLimitChange}
        inputProps={{ min: 1, max: 50 }}
        size="small"
        sx={{ mb: 2, width: 220 }}
        helperText="Choose between 1 and 50"
      />

      {loading && <CircularProgress />}
      {error && <Typography color="error">{error}</Typography>}

      {!loading && !error && (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Customer ID</TableCell>
                <TableCell>Prediction</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {history.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    No predictions yet.
                  </TableCell>
                </TableRow>
              ) : (
                history.map((item, idx) => (
                  <TableRow key={idx}>
                    <TableCell>{item.cutomer_id}</TableCell>
                    <TableCell style={{ color: item.label === 'Churner' ? 'red' : 'green' }}>
                      {item.label}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}

export default PredictionHistory;
