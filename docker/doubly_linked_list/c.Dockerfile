# C: compile a static binary, ship it on distroless "static" -- no shell, no
# package manager, no libc to patch. The runtime image is the binary plus CA
# certs and a passwd file with the nonroot user (uid 65532).
FROM gcc:14 AS build
WORKDIR /src
COPY c/doubly_linked_list/doubly_linked_list.c .
RUN mkdir /out \
 && gcc -std=c11 -Wall -Wextra -Werror -O2 -static \
        -o /out/doubly_linked_list doubly_linked_list.c

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/doubly_linked_list /app/doubly_linked_list
USER 65532:65532
ENTRYPOINT ["/app/doubly_linked_list"]
