// // src/api/api.js
// const API_BASE = 'http://localhost:8000'; // change to database

// export const predictChurn = async (userData) => {
//   const response = await fetch(`${API_BASE}/predict`, {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify(userData),
//   });
//   if (!response.ok) {
//     const text = await response.text();
//     throw new Error(text || 'Prediction failed');
//   }
//   return response.json();
// };

// export const getPredictionHistory = async () => {
//   const response = await fetch(`${API_BASE}/history?limit=20`);
//   if (!response.ok) {
//     const text = await response.text();
//     throw new Error(text || 'Failed to load history');
//   }
//   return response.json(); // expect { predictions: [...] }
// };

// export const submitFeedback = async (feedbackList) => {
//   const response = await fetch(`${API_BASE}/feedback`, {
//     method: 'POST',
//     headers: { 'Content-Type': 'application/json' },
//     body: JSON.stringify({ feedbacks: feedbackList }),
//   });
//   if (!response.ok) {
//     const text = await response.text();
//     throw new Error(text || 'Feedback submission failed');
//   }
//   return response.json();
// };


// src/api/api.js
const USE_MOCK = true; // set to false later when your real APIs are ready
const API_BASE = 'http://localhost:8000';

export const predictChurn = async (userData) => {
  if (USE_MOCK) {
    // fake response
    return {
      label: Number(userData.age) > 40 ? 'Churner' : 'Non-churner',
      churnProbability: Number(userData.age) > 40 ? 0.78 : 0.22,
    };
  }

  const response = await fetch(`${API_BASE}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData),
  });
  if (!response.ok) throw new Error('Prediction failed');
  return response.json();
};

export const getPredictionHistory = async () => {
  if (USE_MOCK) {
    return {
      predictions: [
        {
          timestamp: new Date().toISOString(),
          user_id: '123',
          age: 45,
          tenure: 24,
          balance: 50000,
          num_products: 2,
          credit_score: 650,
          label: 'Churner',
          churnProbability: 0.81,
        },
        {
          timestamp: new Date().toISOString(),
          user_id: '456',
          age: 30,
          tenure: 12,
          balance: 20000,
          num_products: 1,
          credit_score: 720,
          label: 'Non-churner',
          churnProbability: 0.12,
        },
      ],
    };
  }

  const response = await fetch(`${API_BASE}/history?limit=20`);
  if (!response.ok) throw new Error('Failed to load history');
  return response.json();
};

export const submitFeedback = async (feedbackList) => {
  if (USE_MOCK) {
    console.log('Mock feedback received:', feedbackList);
    return { status: 'ok' };
  }

  const response = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ feedbacks: feedbackList }),
  });
  if (!response.ok) throw new Error('Feedback submission failed');
  return response.json();
};
