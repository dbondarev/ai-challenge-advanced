FROM node:20-alpine
WORKDIR /app
COPY trusted/check.cjs /opt/day15/check.cjs
RUN chmod 0555 /opt/day15/check.cjs
USER 1000:1000
CMD ["node", "src/server.js"]
