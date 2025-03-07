import React, { useState } from 'react';
import {
  Typography,
  Box,
  TextField,
  Button,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Divider,
  Chip,
} from '@mui/material';
import { SelectChangeEvent } from '@mui/material/Select';
import StorageIcon from '@mui/icons-material/Storage';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import { apiService } from '../services/apiService';

const ConnectionForm = () => {
  const [dbType, setDbType] = useState('');
  const [connectionString, setConnectionString] = useState('');
  const [host, setHost] = useState('');
  const [port, setPort] = useState('');
  const [database, setDatabase] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
  } | null>(null);
  const [advancedMode, setAdvancedMode] = useState(false);

  const handleDbTypeChange = (event: SelectChangeEvent) => {
    setDbType(event.target.value);
    // Set default port based on database type
    switch (event.target.value) {
      case 'mysql':
        setPort('3306');
        break;
      case 'postgresql':
        setPort('5432');
        break;
      case 'mssql':
        setPort('1433');
        break;
      case 'oracle':
        setPort('1521');
        break;
      case 'sybase':
        setPort('5000');
        break;
      default:
        setPort('');
    }
  };

  const buildConnectionString = () => {
    if (advancedMode) return connectionString;

    switch (dbType) {
      case 'mysql':
        return `mysql+pymysql://${username}:${password}@${host}:${port}/${database}`;
      case 'postgresql':
        return `postgresql://${username}:${password}@${host}:${port}/${database}`;
      case 'mssql':
        return `mssql+pyodbc://${username}:${password}@${host}:${port}/${database}?driver=ODBC+Driver+17+for+SQL+Server`;
      case 'oracle':
        return `oracle+cx_oracle://${username}:${password}@${host}:${port}/?service_name=${database}`;
      case 'sybase':
        return `DRIVER={FreeTDS};SERVER=${host};PORT=${port};DATABASE=${database};UID=${username};PWD=${password};TDS_VERSION=5.0`;
      default:
        return '';
    }
  };

  const handleTestConnection = async () => {
    try {
      setLoading(true);
      setTestResult(null);
      
      const connString = buildConnectionString();
      
      // In a real app, this would be an API call
      // const response = await apiService.testConnection({ connectionString: connString });
      
      // Mock response for now
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Simulate successful connection for Sybase
      if (dbType === 'sybase') {
        setTestResult({
          success: true,
          message: 'Connection successful! Database version: Sybase ASE 16.0',
        });
      } else {
        // Simulate failed connection for other types (for demo purposes)
        setTestResult({
          success: false,
          message: 'Connection failed: Unable to connect to the database server.',
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: `Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExtractSchema = async () => {
    try {
      setLoading(true);
      const connString = buildConnectionString();
      
      // In a real app, this would be an API call
      // await apiService.extractSchema({ connectionString: connString });
      
      // Mock for now
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setTestResult({
        success: true,
        message: 'Schema extraction started successfully! You can view the progress in the Schema Viewer.',
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: `Schema extraction failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Database Connection
      </Typography>
      
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Box display="flex" alignItems="center" mb={3}>
          <StorageIcon color="primary" fontSize="large" />
          <Typography variant="h5" ml={1}>
            Connect to Database
          </Typography>
        </Box>
        
        <Box mb={3}>
          <Button
            variant={advancedMode ? "outlined" : "contained"}
            onClick={() => setAdvancedMode(false)}
            sx={{ mr: 1 }}
          >
            Standard Mode
          </Button>
          <Button
            variant={advancedMode ? "contained" : "outlined"}
            onClick={() => setAdvancedMode(true)}
          >
            Advanced Mode
          </Button>
        </Box>
        
        {advancedMode ? (
          <Box mb={3}>
            <TextField
              label="Connection String"
              fullWidth
              multiline
              rows={4}
              value={connectionString}
              onChange={(e) => setConnectionString(e.target.value)}
              placeholder="e.g., DRIVER={FreeTDS};SERVER=localhost;PORT=5000;DATABASE=SampleDB;UID=sa;PWD=sybase123;TDS_VERSION=5.0"
              helperText="Enter the full connection string for your database"
            />
          </Box>
        ) : (
          <>
            <Grid container spacing={3} mb={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel id="db-type-label">Database Type</InputLabel>
                  <Select
                    labelId="db-type-label"
                    value={dbType}
                    label="Database Type"
                    onChange={handleDbTypeChange}
                  >
                    <MenuItem value="mysql">MySQL</MenuItem>
                    <MenuItem value="postgresql">PostgreSQL</MenuItem>
                    <MenuItem value="mssql">Microsoft SQL Server</MenuItem>
                    <MenuItem value="oracle">Oracle</MenuItem>
                    <MenuItem value="sybase">Sybase ASE</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Host"
                  fullWidth
                  value={host}
                  onChange={(e) => setHost(e.target.value)}
                  placeholder="e.g., localhost or 192.168.1.100"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Port"
                  fullWidth
                  value={port}
                  onChange={(e) => setPort(e.target.value)}
                  placeholder="e.g., 5000"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Database Name"
                  fullWidth
                  value={database}
                  onChange={(e) => setDatabase(e.target.value)}
                  placeholder="e.g., SampleDB"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Username"
                  fullWidth
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g., sa"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Password"
                  fullWidth
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                />
              </Grid>
            </Grid>
            
            <Box mb={3}>
              <Typography variant="subtitle2" gutterBottom>
                Generated Connection String:
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                <code>{buildConnectionString() || 'Select a database type and fill in the details'}</code>
              </Paper>
            </Box>
          </>
        )}
        
        <Box display="flex" gap={2}>
          <Button
            variant="contained"
            onClick={handleTestConnection}
            disabled={loading || (!advancedMode && (!dbType || !host || !database))}
          >
            {loading ? <CircularProgress size={24} /> : 'Test Connection'}
          </Button>
          <Button
            variant="contained"
            color="primary"
            onClick={handleExtractSchema}
            disabled={loading || !testResult?.success}
          >
            Extract Schema
          </Button>
        </Box>
        
        {testResult && (
          <Box mt={3}>
            <Alert 
              severity={testResult.success ? 'success' : 'error'}
              icon={testResult.success ? <CheckCircleOutlineIcon /> : undefined}
            >
              {testResult.message}
            </Alert>
          </Box>
        )}
      </Paper>
      
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Saved Connections
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        <Box display="flex" flexDirection="column" gap={2}>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box>
                <Typography variant="subtitle1">SampleDB (Sybase)</Typography>
                <Typography variant="body2" color="text.secondary">
                  localhost:5000
                </Typography>
              </Box>
              <Box display="flex" gap={1}>
                <Chip label="Connected" color="success" size="small" />
                <Button size="small" variant="outlined">
                  Connect
                </Button>
                <Button size="small" variant="outlined" color="error">
                  Remove
                </Button>
              </Box>
            </Box>
          </Paper>
          
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box>
                <Typography variant="subtitle1">TestDB (Sybase)</Typography>
                <Typography variant="body2" color="text.secondary">
                  192.168.1.100:5000
                </Typography>
              </Box>
              <Box display="flex" gap={1}>
                <Button size="small" variant="outlined">
                  Connect
                </Button>
                <Button size="small" variant="outlined" color="error">
                  Remove
                </Button>
              </Box>
            </Box>
          </Paper>
        </Box>
      </Paper>
    </Box>
  );
};

export default ConnectionForm;
