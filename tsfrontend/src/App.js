import React, { useReducer } from 'react';
import {
  BrowserRouter as Router,
  Switch,
  Route
} from "react-router-dom";
import { Provider } from './providers/provider';
import { reducer } from './reducers/reducer';
import Configuration from "./components/Configuration";
import Data from "./components/Data";
import Error from "./components/Error";
import Navbar from 'react-bootstrap/Navbar';
import Nav from 'react-bootstrap/Nav';
import Container from 'react-bootstrap/Container';


import 'bootstrap/dist/css/bootstrap.min.css';

const initialState = {
  error: false,
  graphData: false,
  configurations: []
}

function App() {
  const state = useReducer(reducer, initialState);
  return (
    <Router>
      <div>
        <Provider value={state}>
          <Container>
            <Error />
          </Container>

          <Container>
            <Navbar bg="dark" variant="dark" expand="lg">
              <Navbar.Brand href="/">DynamoDB Timeseries demo</Navbar.Brand>
              <Navbar.Toggle aria-controls="basic-navbar-nav" />
              <Navbar.Collapse id="basic-navbar-nav">
                <Nav className="mr-auto">
                  <Nav.Link href="/">Data</Nav.Link>
                  <Nav.Link href="/configuration">Configuration</Nav.Link>
                </Nav>
              </Navbar.Collapse>
            </Navbar>
          </Container>

          <Container>
            <Switch>
              <Route path="/configuration">
                <Configuration />
              </Route>
              <Route path="/">
                <Data />
              </Route>
            </Switch>
          </Container>
        </Provider>
      </div>
    </Router>
  );
}

/*

*/

export default App;
