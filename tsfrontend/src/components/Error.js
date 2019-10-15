import React, { useState } from 'react';
import { useGetError } from '../hooks/ErrorHooks';
import { useTranslation } from 'react-i18next';
import i18n from "../i18n/i18n";
import Alert from 'react-bootstrap/Alert';


const Error = () => {
    const error = useGetError()
    return <AlertDismissibleExample error={error} />
}

const AlertDismissibleExample = (props) => {
    const [show, setShow] = useState(true);
    const { t } = useTranslation('errors', { i18n });
    if (show && props.error) {
        return <Alert key={"api-error"} variant={"danger"} dismissible onClose={() => setShow(false)}>
            <span className="alert-message" >{t(props.error)}</span>
        </Alert>
    }
    return null
}

export default Error;