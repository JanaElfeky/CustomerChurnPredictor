import React from 'react';

function tabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && (
        <div style={{ padding: '20px' }}>
          {children}
        </div>
      )}
    </div>
  );
}

export default tabPanel;
