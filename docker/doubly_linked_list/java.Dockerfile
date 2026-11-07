# Java: compile with a full JDK, run on a distroless JRE. The JDK (javac, jshell,
# jlink, ...) never reaches the runtime image.
FROM eclipse-temurin:21-jdk AS build
WORKDIR /src
COPY java/doubly_linked_list/DoublyLinkedListLab.java .
RUN javac -Xlint:all -Werror -d /out DoublyLinkedListLab.java

FROM gcr.io/distroless/java21-debian12:nonroot
COPY --from=build /out /app
USER 65532:65532
# -XX:-UsePerfData: the JVM would otherwise try to write /tmp/hsperfdata_*,
# which is pointless on a read-only filesystem.
ENTRYPOINT ["/usr/bin/java", "-XX:-UsePerfData", "-cp", "/app", "DoublyLinkedListLab"]
