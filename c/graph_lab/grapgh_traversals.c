#include <stdio.h>

#define MAX 100

int adj[MAX][MAX];   // Adjacency matrix to store the graph
int visited[MAX];    // Keeps track of visited vertices
int V, E;            // Number of vertices and edges

// BFS traversal using a queue
void BFS(int start)
{
    int queue[MAX];
    int front = 0, rear = -1;
    int u, v;

    // Initially, mark all vertices as unvisited (0 means unvisited)
    for (int i = 0; i < V; i++)
        visited[i] = 0;

    // Insert the starting vertex into the queue
    queue[++rear] = start;
    visited[start] = 1;

    printf("BFS: ");

    // Continue until the queue becomes empty
    while (front <= rear)
    {
        // Remove the front vertex from the queue
        u = queue[front++];

        // Visit and print the vertex
        printf("%d ", u);
        
        // Check all adjacent vertices in ascending order
        for (v = 0; v < V; v++)
        {
            // If an edge exists and the vertex is unvisited
            if (adj[u][v] == 1 && visited[v] == 0)
            {
                // Insert the adjacent vertex into the queue
                queue[++rear] = v;

                // Mark it as visited to avoid inserting it again
                visited[v] = 1;
            }
        }
    }

    printf("\n");
}

// DFS traversal using a stack
void DFS(int start)
{
    int stack[MAX];
    int top = -1;
    int u, v;

    // Initially, mark all vertices as unvisited
    for (int i = 0; i < V; i++)
        visited[i] = 0;

    // Push the starting vertex onto the stack
    stack[++top] = start;

    printf("DFS: ");

    // Continue until the stack becomes empty
    while (top != -1)
    {
        // Remove the top vertex from the stack
        u = stack[top--];
       
        // Process the vertex only if it is unvisited
        if (visited[u] == 0)
        {
            // Mark the vertex as visited
            visited[u] = 1;

            // Print the visited vertex
            printf("%d ", u);
           
            // Check adjacent vertices in descending order
            // so that the smallest vertex is pushed last and processed first
            for (v = V - 1; v >= 0; v--)
            {
                // If an edge exists and the vertex is unvisited
                if (adj[u][v] == 1 && visited[v] == 0)
                {
                    // Push the adjacent vertex onto the stack
                    stack[++top] = v;
                }
            }
        }
    }

    printf("\n");
}

int main()
{
    int u, v, start;

    // Read the number of vertices and edges
    scanf("%d %d", &V, &E);

    // Read each edge and update the adjacency matrix
    for (int i = 0; i < E; i++)
    {
        scanf("%d %d", &u, &v);

        // The graph is undirected, so add both directions
        adj[u][v] = 1;
        adj[v][u] = 1;
    }

    // Read the starting vertex
    scanf("%d", &start);

    // Perform BFS traversal
    BFS(start);

    // Perform DFS traversal
    DFS(start);

    return 0;
}