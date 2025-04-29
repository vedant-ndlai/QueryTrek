import React, { useState, useEffect, useRef } from 'react';
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
  FormControlLabel,
  Switch,
  Slider,
  TextField,
  SelectChangeEvent,
} from '@mui/material';
import { apiService } from '../services/apiService';
import CytoscapeComponent from 'react-cytoscapejs';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { Core, NodeSingular, EdgeSingular } from 'cytoscape';

// Register the dagre layout
cytoscape.use(dagre);

interface NodeData {
  id: string;
  label: string;
  type: string;
  color?: string;
}

interface EdgeData {
  id?: string;
  source: string;
  target: string;
  label: string;
}

interface CytoscapeProps {
  elements: {
    nodes: Array<{ data: NodeData }>,
    edges: Array<{ data: EdgeData }>
  };
  layout: string;
  showLabels: boolean;
  nodeSize: number;
}

const CytoscapeGraph: React.FC<CytoscapeProps> = ({ elements, layout, showLabels, nodeSize }) => {
  const cyRef = useRef<any>(null);

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'table':
        return '#4CAF50';
      case 'view':
        return '#2196F3';
      case 'procedure':
        return '#FF9800';
      default:
        return '#9E9E9E';
    }
  };

  const cytoscapeStylesheet = [
    {
      selector: 'node',
      style: {
        'background-color': 'data(color)',
        'label': showLabels ? 'data(label)' : '',
        'width': nodeSize,
        'height': nodeSize,
        'font-size': '10px',
        'text-valign': 'center',
        'text-halign': 'center',
        'text-wrap': 'wrap',
      }
    },
    {
      selector: 'edge',
      style: {
        'width': 1,
        'line-color': '#666',
        'target-arrow-color': '#666',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': showLabels ? 'data(label)' : '',
        'font-size': '8px',
        'text-rotation': 'autorotate',
      }
    }
  ];

  const formattedElements = elements ? [
    ...elements.nodes.map((node) => ({
      group: 'nodes' as const,
      data: {
        ...node.data,
        color: getNodeColor(node.data.type),
      }
    })),
    ...elements.edges.map((edge) => ({
      group: 'edges' as const,
      data: {
        ...edge.data,
        id: `${edge.data.source}-${edge.data.target}`,
      }
    }))
  ] : [];

  const layoutConfig = {
    name: layout,
    rankDir: 'TB',
    padding: 50,
    animate: true,
    fit: true,
    nodeDimensionsIncludeLabels: true,
  };

  return (
    <Box sx={{ height: '500px', border: '1px solid #ddd', borderRadius: '4px' }}>
      <CytoscapeComponent
        elements={formattedElements}
        style={{ width: '100%', height: '100%' }}
        layout={layoutConfig}
        stylesheet={cytoscapeStylesheet}
        cy={(cy) => { cyRef.current = cy; }}
      />
    </Box>
  );
};

const DependencyAnalysis: React.FC = () => {
  const [loading, setLoading] = useState(false);
  interface Schema {
    id: string;
    name: string;
    tables: number;
    views: number;
    procedures: number;
    extractedAt: string;
  }

  const [schemas, setSchemas] = useState<Schema[]>([]);
  const [selectedSchema, setSelectedSchema] = useState<string>('');
  const [graphData, setGraphData] = useState<{
    nodes: Array<{ data: NodeData }>,
    edges: Array<{ data: EdgeData }>
  } | null>(null);
  const [layoutType, setLayoutType] = useState<string>('dagre');
  const [showLabels, setShowLabels] = useState<boolean>(true);
  const [nodeSize, setNodeSize] = useState<number>(30);
  const [filterText, setFilterText] = useState<string>('');

  useEffect(() => {
    // Mock data for demonstration
    const mockSchemas = [
      { id: '1', name: 'SampleDB', tables: 12, views: 5, procedures: 8, extractedAt: '2025-03-06T14:30:00' },
      { id: '2', name: 'TestDB', tables: 8, views: 3, procedures: 5, extractedAt: '2025-03-07T09:15:00' },
    ];
    
    setSchemas(mockSchemas);
  }, []);

  const handleSchemaChange = (event: SelectChangeEvent) => {
    const schemaId = event.target.value as string;
    setSelectedSchema(schemaId);
    
    // In a real app, this would be an API call
    // fetchDependencyGraph(schemaId);
    
    // Mock data for demonstration
    setLoading(true);
    setTimeout(() => {
      const mockGraphData = {
        nodes: [
          { data: { id: 'users', label: 'users', type: 'table' } },
          { data: { id: 'orders', label: 'orders', type: 'table' } },
          { data: { id: 'order_items', label: 'order_items', type: 'table' } },
          { data: { id: 'products', label: 'products', type: 'table' } },
          { data: { id: 'categories', label: 'categories', type: 'table' } },
          { data: { id: 'active_users', label: 'active_users', type: 'view' } },
          { data: { id: 'get_user_orders', label: 'get_user_orders', type: 'procedure' } },
        ],
        edges: [
          { data: { source: 'orders', target: 'users', label: 'FK_user_id' } },
          { data: { source: 'order_items', target: 'orders', label: 'FK_order_id' } },
          { data: { source: 'order_items', target: 'products', label: 'FK_product_id' } },
          { data: { source: 'products', target: 'categories', label: 'FK_category_id' } },
          { data: { source: 'active_users', target: 'users', label: 'depends_on' } },
          { data: { source: 'get_user_orders', target: 'users', label: 'depends_on' } },
          { data: { source: 'get_user_orders', target: 'orders', label: 'depends_on' } },
        ],
      };
      setGraphData(mockGraphData);
      setLoading(false);
    }, 1000);
  };

  const handleLayoutChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setLayoutType(event.target.value as string);
  };

  const handleNodeSizeChange = (event: Event, newValue: number | number[]) => {
    setNodeSize(newValue as number);
  };

  const handleFilterChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFilterText(event.target.value);
  };

  const runAnalysis = () => {
    // In a real app, this would trigger a new analysis
    setLoading(true);
    setTimeout(() => {
      // Pretend we got updated data
      setLoading(false);
    }, 1500);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Database Dependency Analysis
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
            <Button 
              variant="contained" 
              disabled={!selectedSchema}
              onClick={runAnalysis}
            >
              Run New Analysis
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : selectedSchema && graphData ? (
        <Box>
          <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Visualization Controls
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={showLabels}
                      onChange={(e) => setShowLabels(e.target.checked)}
                    />
                  }
                  label="Show Labels"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography gutterBottom>Node Size</Typography>
                <Slider
                  value={nodeSize}
                  onChange={(_, value) => setNodeSize(value as number)}
                  min={20}
                  max={60}
                  step={5}
                  marks
                  valueLabelDisplay="auto"
                />
              </Grid>
            </Grid>
          </Paper>

          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Legend
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box
                      sx={{
                        width: 16,
                        height: 16,
                        bgcolor: '#4CAF50',
                        mr: 1,
                        borderRadius: '50%',
                      }}
                    />
                    <Typography variant="body2">Table</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box
                      sx={{
                        width: 16,
                        height: 16,
                        bgcolor: '#2196F3',
                        mr: 1,
                        borderRadius: '50%',
                      }}
                    />
                    <Typography variant="body2">View</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box
                      sx={{
                        width: 16,
                        height: 16,
                        bgcolor: '#FF9800',
                        mr: 1,
                        borderRadius: '50%',
                      }}
                    />
                    <Typography variant="body2">Stored Procedure</Typography>
                  </Box>
                </CardContent>
              </Card>

              <Card sx={{ mt: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    About
                  </Typography>
                  <Typography variant="body2" paragraph>
                    This dependency graph shows the relationships between database objects in the selected schema.
                    Tables are connected through foreign key relationships, while views and procedures depend on
                    the tables they reference.
                    Use the visualization controls to explore different aspects of the schema.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={9}>
              <CytoscapeGraph
                elements={{
                  nodes: graphData.nodes.filter((node) => 
                    filterText === '' || node.data.label.toLowerCase().includes(filterText.toLowerCase())
                  ),
                  edges: graphData.edges
                }}
                layout={layoutType}
                showLabels={showLabels}
                nodeSize={nodeSize}
              />
            </Grid>
          </Grid>
        </Box>
      ) : (
        <Paper elevation={1} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            Select a schema to view its dependency graph
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default DependencyAnalysis;
