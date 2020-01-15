import React from 'react';
import { useGetConfigurations, useSaveConfiguration } from '../hooks/ConfigurationHooks'
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Table from 'react-bootstrap/Table';
import Button from 'react-bootstrap/Button';

export const Configuration = () => {
    const configurations = useGetConfigurations()
    return (
        <div>
            <NewConfigurationForm />
            <ConfigurationTable configurations={configurations} />
        </div>
    )
}

export const NewConfigurationForm = () => {
    const defaultValues = {
        "aggregation": "sum"
    }
    const { inputs, handleInputChange, handleSubmit } = useSaveConfiguration(defaultValues);

    return (
        <Form onSubmit={handleSubmit}>
            <Row>
                <Col>
                    <Form.Label>Name</Form.Label>
                </Col>
                <Col>
                    <Form.Label>Aggregation method</Form.Label>
                </Col>
                <Col>
                </Col>
            </Row>
            <Row>
                <Col><Form.Control name="timeserie" onChange={handleInputChange} value={inputs.timeserie} /></Col>
                <Col><Form.Control as="select" name="aggregation" onChange={handleInputChange} value={inputs.aggregation}>
                    <option value="sum">Sum</option>
                    <option value="last">Last</option>
                    <option value="max">Max</option>
                    <option value="min">Min</option>
                    <option value="average">Average</option>
                    <option value="count">Count</option>
                </Form.Control></Col>
                <Col>
                    <Button variant="primary" type="submit" size="sm">
                        Submit
                    </Button>
                </Col>
            </Row>
        </Form>
    )
}

export const ConfigurationTable = (props) => {
    let rows = []
    for (let conf of props.configurations) {
        rows.push(ConfigurationEntry(conf))
    }

    return (
        <Table>
            <thead>
                <tr>
                    <td>Timeserie name</td>
                    <td>Aggregation method</td>
                    <td>TTL (second)</td>
                    <td>TTL (minute)</td>
                    <td>TTL (hour)</td>
                    <td>TTL (day)</td>
                    <td>TTL (month)</td>
                    <td>TTL (year)</td>
                    <td>Timezone</td>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </Table>
    )
}

export const ConfigurationEntry = (conf) => {
    return <tr key={conf.timeserie}>
        <td>{conf.timeserie}</td>
        <td>{conf.aggregation_method}</td>
        <td>{formatRetention(conf.retentions["second"])}</td>
        <td>{formatRetention(conf.retentions["minute"])}</td>
        <td>{formatRetention(conf.retentions["hour"])}</td>
        <td>{formatRetention(conf.retentions["day"])}</td>
        <td>{formatRetention(conf.retentions["month"])}</td>
        <td>{formatRetention(conf.retentions["year"])}</td>
        <td>{conf.timezone}</td>
    </tr>
}

export const formatRetention = (retentionSeconds) => {
    //TODO: How to format properly
    //const day = retentionSeconds / (24 * 3600)
    //return `${day} days` 
    return retentionSeconds
}

export default Configuration;