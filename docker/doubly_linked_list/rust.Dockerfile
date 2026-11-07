# Rust: compile with the full toolchain, ship on distroless "cc" (glibc and
# libgcc only). bookworm on both sides so the glibc versions match.
FROM rust:1-slim-bookworm AS build
WORKDIR /src
COPY rust/doubly_linked_list/doubly_linked_list.rs .
RUN mkdir /out \
 && rustc -O --edition 2021 -D warnings -o /out/doubly_linked_list doubly_linked_list.rs

FROM gcr.io/distroless/cc-debian12:nonroot
COPY --from=build /out/doubly_linked_list /app/doubly_linked_list
USER 65532:65532
ENTRYPOINT ["/app/doubly_linked_list"]
