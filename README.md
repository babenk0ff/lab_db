# lab_db

### For dev

1. Rename *.env.dev-sample* to *.env.dev*.
2. Build and run containers:

   ```bash
   docker compose up -d --build
   ```
3. The app will be available at [http://localhost:8000](http://localhost:8000).

### For prod

1. Rename *.env.prod-sample* to *.env.prod*.
2. Specify required environment variables in *.env.dev*.
3. Build and run containers:

   ```bash
   docker compose -f docker-compose.full.yml up -d --build
   ```
4. Run migrations:

   ```
   docker compose -f docker-compose.prod.yml exec backend python manage.py makemigrations
   ```
5. Collect static:
   ```
   docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --no-input
   ```
