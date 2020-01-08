FROM rodolpheche/wiremock

EXPOSE 8080 8443
ADD https://repo1.maven.org/maven2/com/opentable/wiremock-body-transformer/1.1.6/wiremock-body-transformer-1.1.6.jar /var/wiremock/extensions/

COPY __files /home/wiremock/__files
COPY mappings /home/wiremock/mappings

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["java", "-cp", "/var/wiremock/lib/*:/var/wiremock/extensions/*", "com.github.tomakehurst.wiremock.standalone.WireMockServerRunner", "--local-response-templating", "--max-request-journal-entries", "100"]
