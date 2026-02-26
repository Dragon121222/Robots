// renderer.cpp
// Software rasterizer using math3d.
// Build: g++ -O2 -o renderer renderer.cpp $(sdl2-config --cflags --libs)
// Controls: WASD = move, QE = up/down, mouse = look, ESC = quit

#include <SDL2/SDL.h>
#include <cmath>
#include <cstring>
#include <cfloat>
#include <cstdint>
#include <vector>
#include <algorithm>

// ─── math3d ──────────────────────────────────────────────────────────────────

namespace math3d {

struct vec3d {
    float x, y, z;

    vec3d operator+(const vec3d& r) const { return {x+r.x, y+r.y, z+r.z}; }
    vec3d operator-(const vec3d& r) const { return {x-r.x, y-r.y, z-r.z}; }
    vec3d operator*(float s)        const { return {x*s, y*s, z*s}; }
    vec3d operator/(float s)        const { return {x/s, y/s, z/s}; }
    vec3d& operator+=(const vec3d& r) { x+=r.x; y+=r.y; z+=r.z; return *this; }

    float length()     const { return sqrtf(x*x + y*y + z*z); }
    vec3d normalized() const { return *this / length(); }

    static float dot(const vec3d& a, const vec3d& b) {
        return a.x*b.x + a.y*b.y + a.z*b.z;
    }
    static vec3d cross(const vec3d& a, const vec3d& b) {
        return {
            a.y*b.z - a.z*b.y,
            a.z*b.x - a.x*b.z,
            a.x*b.y - a.y*b.x
        };
    }
};

struct mat4 {
    float m[4][4]; // column-major: m[col][row]

    static mat4 identity() {
        mat4 r{};
        for (int i = 0; i < 4; i++) r.m[i][i] = 1.0f;
        return r;
    }

    mat4 operator*(const mat4& b) const {
        mat4 r{};
        for (int col = 0; col < 4; col++)
            for (int row = 0; row < 4; row++)
                for (int k = 0; k < 4; k++)
                    r.m[col][row] += m[k][row] * b.m[col][k];
        return r;
    }

    vec3d operator*(const vec3d& v) const {
        float x = v.x*m[0][0] + v.y*m[1][0] + v.z*m[2][0] + m[3][0];
        float y = v.x*m[0][1] + v.y*m[1][1] + v.z*m[2][1] + m[3][1];
        float z = v.x*m[0][2] + v.y*m[1][2] + v.z*m[2][2] + m[3][2];
        float w = v.x*m[0][3] + v.y*m[1][3] + v.z*m[2][3] + m[3][3];
        return {x/w, y/w, z/w};
    }

    vec3d transform_dir(const vec3d& v) const {
        return {
            v.x*m[0][0] + v.y*m[1][0] + v.z*m[2][0],
            v.x*m[0][1] + v.y*m[1][1] + v.z*m[2][1],
            v.x*m[0][2] + v.y*m[1][2] + v.z*m[2][2]
        };
    }
};

static mat4 translate(const vec3d& t) {
    mat4 r = mat4::identity();
    r.m[3][0] = t.x; r.m[3][1] = t.y; r.m[3][2] = t.z;
    return r;
}

static mat4 rotateY(float a) {
    mat4 r = mat4::identity();
    float c = cosf(a), s = sinf(a);
    r.m[0][0] =  c; r.m[2][0] =  s;
    r.m[0][2] = -s; r.m[2][2] =  c;
    return r;
}

static mat4 rotateX(float a) {
    mat4 r = mat4::identity();
    float c = cosf(a), s = sinf(a);
    r.m[1][1] =  c; r.m[2][1] =  s;
    r.m[1][2] = -s; r.m[2][2] =  c;
    return r;
}

static mat4 perspective(float fov, float aspect, float near, float far) {
    mat4 r{};
    float f = 1.0f / tanf(fov * 0.5f);
    r.m[0][0] = f / aspect;
    r.m[1][1] = f;
    r.m[2][2] = (far + near) / (near - far);
    r.m[2][3] = -1.0f;
    r.m[3][2] = (2.0f * far * near) / (near - far);
    return r;
}

static mat4 look_at(const vec3d& eye, const vec3d& target, const vec3d& up) {
    vec3d f = (target - eye).normalized();
    vec3d r = vec3d::cross(f, up).normalized();
    vec3d u = vec3d::cross(r, f);
    mat4 m{};
    m.m[0][0] =  r.x; m.m[1][0] =  r.y; m.m[2][0] =  r.z;
    m.m[0][1] =  u.x; m.m[1][1] =  u.y; m.m[2][1] =  u.z;
    m.m[0][2] = -f.x; m.m[1][2] = -f.y; m.m[2][2] = -f.z;
    m.m[3][0] = -vec3d::dot(r, eye);
    m.m[3][1] = -vec3d::dot(u, eye);
    m.m[3][2] =  vec3d::dot(f, eye);
    m.m[3][3] = 1.0f;
    return m;
}

} // namespace math3d

// ─── framebuffer ─────────────────────────────────────────────────────────────

constexpr int W = 1280;
constexpr int H = 720;

static uint32_t fb[W * H];
static float    db[W * H]; // depth buffer

inline void fb_clear(uint32_t color) {
    for (int i = 0; i < W*H; i++) { fb[i] = color; db[i] = FLT_MAX; }
}

inline void fb_set(int x, int y, float depth, uint32_t color) {
    if (x < 0 || x >= W || y < 0 || y >= H) return;
    int idx = y * W + x;
    if (depth < db[idx]) { db[idx] = depth; fb[idx] = color; }
}

// ─── rasterizer ──────────────────────────────────────────────────────────────

struct Vertex {
    math3d::vec3d pos; // NDC after MVP
    float depth;       // pre-divide z for depth buffer
    uint32_t color;
};

// Edge function: positive when p is to the left of (a→b)
inline float edge(float ax, float ay, float bx, float by, float px, float py) {
    return (bx - ax) * (py - ay) - (by - ay) * (px - ax);
}

void draw_triangle(const Vertex& v0, const Vertex& v1, const Vertex& v2) {
    // NDC → screen
    auto to_screen = [](float ndc, int dim) -> float {
        return (ndc * 0.5f + 0.5f) * dim;
    };

    float sx0 = to_screen(v0.pos.x, W), sy0 = to_screen(-v0.pos.y, H);
    float sx1 = to_screen(v1.pos.x, W), sy1 = to_screen(-v1.pos.y, H);
    float sx2 = to_screen(v2.pos.x, W), sy2 = to_screen(-v2.pos.y, H);

    // Backface cull
    if (edge(sx0, sy0, sx1, sy1, sx2, sy2) <= 0) return;

    // Bounding box
    int minx = (int)std::max(0.f,    std::min({sx0, sx1, sx2}));
    int maxx = (int)std::min((float)(W-1), std::max({sx0, sx1, sx2}));
    int miny = (int)std::max(0.f,    std::min({sy0, sy1, sy2}));
    int maxy = (int)std::min((float)(H-1), std::max({sy0, sy1, sy2}));

    float area = edge(sx0, sy0, sx1, sy1, sx2, sy2);
    if (area == 0) return;

    for (int y = miny; y <= maxy; y++) {
        for (int x = minx; x <= maxx; x++) {
            float px = x + 0.5f, py = y + 0.5f;
            float w0 = edge(sx1, sy1, sx2, sy2, px, py);
            float w1 = edge(sx2, sy2, sx0, sy0, px, py);
            float w2 = edge(sx0, sy0, sx1, sy1, px, py);
            if (w0 < 0 || w1 < 0 || w2 < 0) continue;
            w0 /= area; w1 /= area; w2 /= area;

            float depth = w0*v0.depth + w1*v1.depth + w2*v2.depth;

            // Interpolate color channels
            uint8_t r = (uint8_t)(w0*((v0.color>>16)&0xff) + w1*((v1.color>>16)&0xff) + w2*((v2.color>>16)&0xff));
            uint8_t g = (uint8_t)(w0*((v0.color>> 8)&0xff) + w1*((v1.color>> 8)&0xff) + w2*((v2.color>> 8)&0xff));
            uint8_t b = (uint8_t)(w0*((v0.color    )&0xff) + w1*((v1.color    )&0xff) + w2*((v2.color    )&0xff));

            fb_set(x, y, depth, 0xFF000000 | (r<<16) | (g<<8) | b);
        }
    }
}

// ─── scene ───────────────────────────────────────────────────────────────────

// Cube: 8 verts, 12 triangles (6 faces × 2)
static const math3d::vec3d cube_verts[8] = {
    {-1,-1,-1}, { 1,-1,-1}, { 1, 1,-1}, {-1, 1,-1},
    {-1,-1, 1}, { 1,-1, 1}, { 1, 1, 1}, {-1, 1, 1},
};

// Per-face colors (flat)
static const uint32_t face_colors[6] = {
    0xFFE74C3C, // -Z red
    0xFF3498DB, // +Z blue
    0xFF2ECC71, // -X green
    0xFFE67E22, // +X orange
    0xFFECF0F1, // -Y white
    0xFF9B59B6, // +Y purple
};

// (v0,v1,v2,v3) quad indices → 2 CCW triangles (right-hand, front face = CCW from outside)
static const int cube_quads[6][4] = {
    {0,3,2,1}, // -Z
    {4,5,6,7}, // +Z
    {0,4,7,3}, // -X
    {1,2,6,5}, // +X
    {0,1,5,4}, // -Y
    {3,7,6,2}, // +Y
};

void draw_cube(const math3d::mat4& mvp, const math3d::mat4& model,
               const math3d::vec3d& light_dir)
{
    for (int f = 0; f < 6; f++) {
        // Face normal in world space (flat shading)
        math3d::vec3d face_verts[4];
        for (int i = 0; i < 4; i++)
            face_verts[i] = model * cube_verts[cube_quads[f][i]];

        math3d::vec3d normal = math3d::vec3d::cross(
            face_verts[1] - face_verts[0],
            face_verts[2] - face_verts[0]
        ).normalized();

        float diffuse = std::max(0.15f, math3d::vec3d::dot(normal, light_dir));

        uint32_t fc = face_colors[f];
        uint8_t r = (uint8_t)(((fc>>16)&0xff) * diffuse);
        uint8_t g = (uint8_t)(((fc>> 8)&0xff) * diffuse);
        uint8_t b = (uint8_t)(((fc    )&0xff) * diffuse);
        uint32_t shaded = 0xFF000000 | (r<<16) | (g<<8) | b;

        // Project 4 verts
        Vertex pv[4];
        for (int i = 0; i < 4; i++) {
            math3d::vec3d v = cube_verts[cube_quads[f][i]];
            // Need w for depth — do MVP manually to keep w
            float wx = v.x*mvp.m[0][0]+v.y*mvp.m[1][0]+v.z*mvp.m[2][0]+mvp.m[3][0];
            float wy = v.x*mvp.m[0][1]+v.y*mvp.m[1][1]+v.z*mvp.m[2][1]+mvp.m[3][1];
            float wz = v.x*mvp.m[0][2]+v.y*mvp.m[1][2]+v.z*mvp.m[2][2]+mvp.m[3][2];
            float ww = v.x*mvp.m[0][3]+v.y*mvp.m[1][3]+v.z*mvp.m[2][3]+mvp.m[3][3];
            pv[i] = {{wx/ww, wy/ww, wz/ww}, wz/ww, shaded};
        }

        // Two triangles per quad
        draw_triangle(pv[0], pv[1], pv[2]);
        draw_triangle(pv[0], pv[2], pv[3]);
    }
}

// ─── main ────────────────────────────────────────────────────────────────────

int main() {
    SDL_Init(SDL_INIT_VIDEO);
    SDL_Window*   win = SDL_CreateWindow("renderer", SDL_WINDOWPOS_CENTERED,
                                         SDL_WINDOWPOS_CENTERED, W, H, 0);
    SDL_Renderer* ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED);
    SDL_Texture*  tex = SDL_CreateTexture(ren, SDL_PIXELFORMAT_ARGB8888,
                                           SDL_TEXTUREACCESS_STREAMING, W, H);
    SDL_SetRelativeMouseMode(SDL_TRUE);

    // Camera state
    math3d::vec3d cam_pos = {0, 0, 5};
    float yaw = 0, pitch = 0;

    float cube_angle = 0;
    const math3d::vec3d light_dir = math3d::vec3d{1,2,3}.normalized();

    uint32_t last = SDL_GetTicks();
    bool running = true;

    while (running) {
        uint32_t now = SDL_GetTicks();
        float dt = (now - last) / 1000.0f;
        last = now;

        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) running = false;
            if (e.type == SDL_KEYDOWN && e.key.keysym.sym == SDLK_ESCAPE) running = false;
            if (e.type == SDL_MOUSEMOTION) {
                yaw   -= e.motion.xrel * 0.002f;
                pitch -= e.motion.yrel * 0.002f;
                pitch = std::max(-1.5f, std::min(1.5f, pitch));
            }
        }

        // WASD + QE movement in camera-local space
        const uint8_t* keys = SDL_GetKeyboardState(nullptr);
        float speed = 3.0f * dt;
        math3d::vec3d forward = {sinf(yaw)*cosf(pitch), -sinf(pitch), -cosf(yaw)*cosf(pitch)};
        math3d::vec3d right   = {cosf(yaw), 0, sinf(yaw)};
        math3d::vec3d up      = {0, 1, 0};

        if (keys[SDL_SCANCODE_W]) cam_pos += forward * speed;
        if (keys[SDL_SCANCODE_S]) cam_pos = cam_pos - forward * speed;
        if (keys[SDL_SCANCODE_A]) cam_pos = cam_pos - right * speed;
        if (keys[SDL_SCANCODE_D]) cam_pos += right * speed;
        if (keys[SDL_SCANCODE_Q]) cam_pos = cam_pos - up * speed;
        if (keys[SDL_SCANCODE_E]) cam_pos += up * speed;

        cube_angle += dt * 0.8f;

        // Matrices
        math3d::mat4 model = math3d::rotateY(cube_angle) * math3d::rotateX(cube_angle * 0.4f);
        math3d::mat4 view  = math3d::look_at(cam_pos, cam_pos + forward, up);
        math3d::mat4 proj  = math3d::perspective(1.0472f, (float)W/H, 0.1f, 100.0f);
        math3d::mat4 mvp   = proj * view * model;

        fb_clear(0xFF1A1A2E);
        draw_cube(mvp, model, light_dir);

        SDL_UpdateTexture(tex, nullptr, fb, W * sizeof(uint32_t));
        SDL_RenderCopy(ren, tex, nullptr, nullptr);
        SDL_RenderPresent(ren);
    }

    SDL_DestroyTexture(tex);
    SDL_DestroyRenderer(ren);
    SDL_DestroyWindow(win);
    SDL_Quit();
    return 0;
}