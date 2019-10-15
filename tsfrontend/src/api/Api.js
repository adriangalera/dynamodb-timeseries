const baseApiUrl =   process.env.REACT_APP_API_URL ||   "http://localhost:9999"

const handleError = (err) => {
    console.log(err)
    return undefined
}

export const fetchConfigurations = () => {
    return fetch(baseApiUrl + "/configuration")
        .then(res => res.json()).catch((err) => handleError(err))
}

export const saveConfiguration = (newConfiguration) => {
    return fetch(baseApiUrl + "/configuration", {
        method: 'post',
        body: JSON.stringify(newConfiguration)
    }).then((res) => res.json()).catch((err) => handleError(err))
}

export const fetchGraphData = (request) => {
    /*
    request: {
        timeserie: "timeserie",
        start: unix timestamp start
        end: unix timestamp end
        granularity: "second"
    }
    */

    const fetchDataUrl = `${baseApiUrl}/data/${request.timeserie}/${request.granularity}?start=${request.start}&end=${request.end}`
    return fetch(fetchDataUrl)
        .then(res => res.json())
        .catch((err) => handleError(err))

}

export const putNewData = (timeserie, data) => {
    const putDataUrl = `${baseApiUrl}/data`
    const newDataReq = { timeserie: data }
    return fetch(putDataUrl, {
        method: 'post',
        body: JSON.stringify(newDataReq)
    }).then((res) => res.json()).catch((err) => handleError(err))
}