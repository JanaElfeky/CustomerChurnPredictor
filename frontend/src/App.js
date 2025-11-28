import React, { useState } from 'react';
import { Box, Typography, Tabs, Tab } from '@mui/material';
import GetPrediction from './prediction';
import PredictionHistory from './history';
import FeedbackForm from './feedback';
import TabPanel from './tabs';

function App() {
  const [tabValue, setTabValue] = useState(0);

  const handleChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 1200, mx: 'auto', mt: 4 }}>
      <Typography variant="h4" align="center" gutterBottom>
        Bank Churn Prediction Dashboard
      </Typography>

      <Tabs value={tabValue} onChange={handleChange} centered>
        <Tab label="Get Prediction" />
        <Tab label="Prediction History" />
        <Tab label="Submit Feedback" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <GetPrediction />
      </TabPanel>
      <TabPanel value={tabValue} index={1}>
        <PredictionHistory />
      </TabPanel>
      <TabPanel value={tabValue} index={2}>
        <FeedbackForm />
      </TabPanel>
    </Box>
  );
}

export default App;
