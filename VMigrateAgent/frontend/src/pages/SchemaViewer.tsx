import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Button,
  Card,
  CardContent,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { apiService } from '../services/apiService';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`schema-tabpanel-${index}`}
      aria-labelledby={`schema-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const SchemaViewer = () => {
  const [loading, setLoading] = useState(false);
  const [schemas, setSchemas] = useState<any[]>([]);
  const [selectedSchema, setSelectedSchema] = useState<string>('');
  const [schemaDetails, setSchemaDetails] = useState<any>(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    // Mock data for demonstration
    const mockSchemas = [
      { id: '1', name: 'SampleDB', tables: 12, views: 5, procedures: 8, extractedAt: '2025-03-06T14:30:00' },
      { id: '2', name: 'TestDB', tables: 8, views: 3, procedures: 5, extractedAt: '2025-03-07T09:15:00' },
    ];
    
    setSchemas(mockSchemas);
  }, []);

  const handleSchemaChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    const schemaId = event.target.value as string;
    setSelectedSchema(schemaId);
    
    // In a real app, this would be an API call
    // fetchSchemaDetails(schemaId);
    
    // Mock data for demonstration
    setLoading(true);
    setTimeout(() => {
      const mockDetails = {
        id: schemaId,
        name: schemaId === '1' ? 'SampleDB' : 'TestDB',
        tables: [
          { name: 'users', columns: [
            { name: 'id', type: 'int', nullable: false, isPrimary: true },
            { name: 'username', type: 'varchar(50)', nullable: false },
            { name: 'email', type: 'varchar(100)', nullable: false },
            { name: 'created_at', type: 'datetime', nullable: true },
          ]},
          { name: 'orders', columns: [
            { name: 'id', type: 'int', nullable: false, isPrimary: true },
            { name: 'user_id', type: 'int', nullable: false, isForeignKey: true },
            { name: 'order_date', type: 'datetime', nullable: false },
            { name: 'status', type: 'varchar(20)', nullable: false },
          ]},
        ],
        views: [
          { name: 'active_users', definition: 'SELECT * FROM users WHERE last_login > DATEADD(day, -30, GETDATE())' },
        ],
        procedures: [
          { name: 'get_user_orders', parameters: [
            { name: '@user_id', type: 'int', mode: 'IN' }
          ], returnType: 'TABLE' },
        ],
      };
      setSchemaDetails(mockDetails);
      setLoading(false);
    }, 1000);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Schema Viewer
      </Typography>
      
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel id="schema-select-label">Select Schema</InputLabel>
              <Select
                labelId="schema-select-label"
                id="schema-select"
                value={selectedSchema}
                label="Select Schema"
                onChange={handleSchemaChange as any}
              >
                <MenuItem value="">
                  <em>Select a schema</em>
                </MenuItem>
                {schemas.map((schema) => (
                  <MenuItem key={schema.id} value={schema.id}>
                    {schema.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <Button variant="contained" disabled={!selectedSchema}>
              Extract New Schema
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
          <CircularProgress />
        </Box>
      ) : selectedSchema ? (
        <Box>
          <Paper elevation={3}>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              aria-label="schema tabs"
              variant="fullWidth"
            >
              <Tab label="Tables" />
              <Tab label="Views" />
              <Tab label="Stored Procedures" />
            </Tabs>
            
            <TabPanel value={tabValue} index={0}>
              {schemaDetails?.tables.map((table: any) => (
                <Card key={table.name} sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {table.name}
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Column</TableCell>
                            <TableCell>Type</TableCell>
                            <TableCell>Nullable</TableCell>
                            <TableCell>Key</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {table.columns.map((column: any) => (
                            <TableRow key={column.name}>
                              <TableCell>{column.name}</TableCell>
                              <TableCell>{column.type}</TableCell>
                              <TableCell>{column.nullable ? 'Yes' : 'No'}</TableCell>
                              <TableCell>
                                {column.isPrimary ? 'PK' : column.isForeignKey ? 'FK' : ''}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              ))}
            </TabPanel>
            
            <TabPanel value={tabValue} index={1}>
              {schemaDetails?.views.map((view: any) => (
                <Card key={view.name} sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {view.name}
                    </Typography>
                    <Typography variant="subtitle2" gutterBottom>
                      Definition:
                    </Typography>
                    <Paper elevation={1} sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {view.definition}
                      </pre>
                    </Paper>
                  </CardContent>
                </Card>
              ))}
            </TabPanel>
            
            <TabPanel value={tabValue} index={2}>
              {schemaDetails?.procedures.map((proc: any) => (
                <Card key={proc.name} sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {proc.name}
                    </Typography>
                    <Typography variant="subtitle2" gutterBottom>
                      Parameters:
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Name</TableCell>
                            <TableCell>Type</TableCell>
                            <TableCell>Mode</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {proc.parameters.map((param: any) => (
                            <TableRow key={param.name}>
                              <TableCell>{param.name}</TableCell>
                              <TableCell>{param.type}</TableCell>
                              <TableCell>{param.mode}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                    <Typography variant="subtitle2" sx={{ mt: 2 }}>
                      Return Type: {proc.returnType}
                    </Typography>
                  </CardContent>
                </Card>
              ))}
            </TabPanel>
          </Paper>
        </Box>
      ) : (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            Select a schema to view its details
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default SchemaViewer;
