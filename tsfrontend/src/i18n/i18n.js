import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";

i18n.use(LanguageDetector).init({
    // we init with resources
    resources: {
        en: {
            errors: {
                ADD_CONFIGURATION: "Error saving configuration",
                SET_CONFIGURATIONS: "Error getting configuration",
                SET_GRAPH_DATA: "Error getting timeseries data",
            }
        },
    },
    fallbackLng: "en",
    ns: ["errors"],
    defaultNS: "errors",
    keySeparator: false, // we use content as keys
    interpolation: {
        escapeValue: false, // not needed for react!!
        formatSeparator: ","
    },
    react: {
        wait: true
    }
})

export default i18n;