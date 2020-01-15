import React from 'react';
import { useGetConfigurations } from '../hooks/ConfigurationHooks';
import { useSelectorHook, useGraphData } from '../hooks/DataHooks'
import ReactEcharts from 'echarts-for-react';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
//import DatePicker from 'react-datepicker'
//import "react-datepicker/dist/react-datepicker.css";


const Data = () => {
    return (<div>
        <Selectors></Selectors>
        <Chart />
    </div>
    )
}

export const Selectors = () => {
    const configurations = useGetConfigurations()
    const timeseries = configurations.map(configuration => configuration.timeserie)
    let defaultValues = {
        "timeserie": timeseries[0],
        "from": "",
        "to": "",
        "granularity": "second",
        "quickinternvals": "last_10_seconds"
    }
    const { inputs, handleInputChange, handleSubmit } = useSelectorHook(defaultValues);
    if (inputs.timeserie === undefined && timeseries[0]) {
        handleInputChange({
            persist: () => { },
            target: {
                name: "timeserie",
                value: timeseries[0]
            }
        })
    }

    return <Form onSubmit={handleSubmit}>
        <Row>
            <Col>
                <Form.Label>Timeseries</Form.Label>
            </Col>
            {/*
            <Col>
                <Form.Label>From</Form.Label>
            </Col>
            <Col>
                <Form.Label>To</Form.Label>
            </Col>
            */}
            <Col>
                <Form.Label>Query from</Form.Label>
            </Col>
            {/*
            <Col>
                <Form.Label>Granularitiy</Form.Label>
            </Col>
            */}
            <Col></Col>
        </Row>
        <Row>
            <Col>
                <Form.Control as="select" name="timeserie" onChange={handleInputChange} value={inputs.timeserie}>
                    {timeseries.map(ts => <option key={ts}>{ts}</option>)}
                </Form.Control>
            </Col>
            {/*
            <Col>
                <DatePicker name="from" autoComplete='off'
                    selected={inputs.from}
                    onChange={(date) => handleInputChange({ persist: () => { }, target: { name: 'from', value: date } })} />
            </Col>
            <Col>
                <DatePicker name="to" autoComplete='off'
                    selected={inputs.to}
                    onChange={(date) => handleInputChange({ persist: () => { }, target: { name: 'to', value: date } })} />
            </Col>
            */}
            <Col>
                <Form.Control as="select" name="quickinternvals" onChange={handleInputChange} value={inputs.quickinternvals}>
                    <option value="last_10_seconds">10 seconds ago (seconds)</option>
                    <option value="last_5_minutes">5 minutes ago (minutes)</option>
                    <option value="last_2_hour">2 hours ago (hours)</option>
                </Form.Control>
            </Col>
            {/*
            <Col>
                <Form.Control as="select" name="granularity" onChange={handleInputChange} value={inputs.granularity}>
                    <option value="second">Second</option>
                    <option value="minute">Minute</option>
                    <option value="hour">Hour</option>
                    <option value="day">Day</option>
                    <option value="month">Month</option>
                    <option value="year">Year</option>
                </Form.Control>
            </Col>
            */}
            <Col>
                <Button variant="primary" type="submit" size="sm">
                    Search
                </Button>
            </Col>
        </Row>
    </Form>
}

export const Chart = () => {
    const graphConfiguration = useGraphData()
    if (graphConfiguration) {
        return <ReactEcharts option={graphConfiguration} />
    }
    return null
}

export const extractTimeseriesFromConfiguration = (configurations) => {
    return configurations.map(configuration => configuration.timeserie)
}

export default Data;