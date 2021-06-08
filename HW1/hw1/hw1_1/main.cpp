#include <iostream>
#include <fstream>
#include <stdio.h>
#include <string.h>
#include <cstdlib>
#include <pthread.h>
#include <queue>

#define _ ios::sync_with_stdio(0); cin.tie(0);

using namespace std;

struct Customer{
    int cid;
    int arrive_time;
    int play_round;
    int rest_time;
    int total_play_round;
    bool isfinish;
    bool in_queue;
};

struct Shared_Stack{
	pthread_mutex_t	mutex;
	pthread_cond_t cond;
	int	timer;
    int guarantee_num;
    int next_cid;
    int finish_num;
    int keep_round;
    bool is_playing;
}shared_stack;

int format_num(char ch[]);
void *claw(void *param);
void pop_one(void);
void timer_plus(void);
void push_one(int cid);
Customer *customer;
int customer_num;
queue<int> q_line;

int main(int argc, char *argv[]){
    FILE *file;
    char str[20];
    shared_stack.timer = 0;
    shared_stack.next_cid = -1; // default null
    shared_stack.is_playing = false;
    
    // read file
    file = fopen(argv[1], "r");
    if(file == NULL)
        cout << "file open fail!" << endl;
    else{
        fscanf(file, "%s", str);
        shared_stack.guarantee_num = format_num(str);
        shared_stack.keep_round = shared_stack.guarantee_num;
        fscanf(file, "%s", str);
        customer_num = format_num(str);
        customer = new Customer[customer_num+1];

        for(int i = 1; i <= customer_num; i++){
            customer[i].isfinish = false;
            customer[i].in_queue = false;
            customer[i].cid = i;
            fscanf(file, "%s", str);
            customer[i].arrive_time = format_num(str);
            fscanf(file, "%s", str);
            customer[i].play_round = format_num(str);
            fscanf(file, "%s", str);
            customer[i].rest_time = format_num(str);
            fscanf(file, "%s", str);
            customer[i].total_play_round = format_num(str);
        }
    }

    bool need_wait = false; // for many people in the first time
    for(int i = 1; i <= customer_num; i++){
        if(!need_wait && customer[i].arrive_time == 0){
            q_line.push(i);
            customer[i].in_queue = true;
            need_wait = true;
        }
        else if(need_wait && customer[i].arrive_time == 0){
            push_one(i);
        }
    }

    pthread_t tid;
    (void) pthread_cond_init(&shared_stack.cond, NULL);
    (void) pthread_mutex_init(&shared_stack.mutex, NULL);

    // for the first condition
    pop_one();
    // create thread
    for (int i = 1; i <= customer_num; i++){
        pthread_create(&tid, NULL, claw, &customer[i].cid);
    }

    pthread_join(tid, NULL);

    return 0;
}

void timer_plus(void){
    shared_stack.timer++;
    for(int i = 1; i <= customer_num; i++){
        if(!customer[i].isfinish && !customer[i].in_queue && customer[i].arrive_time <= shared_stack.timer){
            push_one(i);
        }
    }
}

void push_one(int cid){
    if(!q_line.empty() || shared_stack.is_playing) // not empty, must wait in line
        printf("%d %d wait in line\n", shared_stack.timer, cid);
    q_line.push(cid);
    customer[cid].in_queue = true;
}

void pop_one(void){
    // check line is idle or not
    while(q_line.empty()){
        shared_stack.keep_round = shared_stack.guarantee_num; // reset 
        timer_plus();
    }
    // pop one and broadcast
    shared_stack.next_cid = q_line.front();
    customer[q_line.front()].in_queue = false;
    q_line.pop();
    (void) pthread_cond_broadcast(&shared_stack.cond);
    (void) pthread_mutex_unlock(&shared_stack.mutex);
}

int play_round(int cid){
    printf("%d %d start playing\n", shared_stack.timer, cid);
    shared_stack.is_playing = true;
    if(customer[cid].play_round < shared_stack.keep_round && customer[cid].play_round < customer[cid].total_play_round){
        // rest play_round
        customer[cid].in_queue = true;
        for(int i = 1; i <= customer[cid].play_round; i++){
            timer_plus();
            shared_stack.keep_round--;
        }
        customer[cid].arrive_time = shared_stack.timer + customer[cid].rest_time;
        customer[cid].total_play_round -= customer[cid].play_round; 
        customer[cid].in_queue = false;
        shared_stack.is_playing = false;

        return 1; 
    }
    else if(customer[cid].play_round >= customer[cid].total_play_round && customer[cid].play_round < shared_stack.keep_round){
        // play total_play_round
        customer[cid].isfinish = true;
        for(int i = 1; i <= customer[cid].total_play_round; i++)
            timer_plus();
    }
    else if(customer[cid].play_round >= shared_stack.keep_round && customer[cid].play_round < customer[cid].total_play_round){
        // play keep_round
        customer[cid].isfinish = true;
        for(int i = 1; i <= shared_stack.keep_round; i++)
            timer_plus();
    }
    else if(customer[cid].play_round >= customer[cid].total_play_round && customer[cid].total_play_round >= shared_stack.keep_round){
        // play keep_round
        customer[cid].isfinish = true;
        for(int i = 1; i <= shared_stack.keep_round; i++)
            timer_plus();      
    } 
    else if(customer[cid].play_round >= shared_stack.keep_round && shared_stack.keep_round >= customer[cid].total_play_round){
        // play total_play_round
        customer[cid].isfinish = true;
        for(int i = 1; i <= customer[cid].total_play_round; i++)
            timer_plus();
    }
    else{
        cout << "whats? exceptions occur!" << endl;
    }
    printf("%d %d finish playing YES\n", shared_stack.timer, cid);
    shared_stack.keep_round = shared_stack.guarantee_num; // finish reset
    shared_stack.is_playing = false;
    return 0; // finish
}

void *claw(void *param){
    int cid = *(int *)param;
    bool redo = false;
    while(1){
        redo = false;
        (void) pthread_mutex_lock(&shared_stack.mutex);

        while(shared_stack.next_cid != customer[cid].cid){
            // you are not next one, wait for the cond_variable
            (void) pthread_cond_wait(&shared_stack.cond, &shared_stack.mutex);
        }

        // rest several rounds
        while(play_round(cid) == 1){
            printf("%d %d finish playing NO\n", shared_stack.timer, cid);
            // check line is idle or not
            while(q_line.empty()){
                shared_stack.keep_round = shared_stack.guarantee_num; // reset 
                timer_plus();
            }

            // if next one is itself
            if(q_line.front() == shared_stack.next_cid){
                customer[q_line.front()].in_queue = false;
                q_line.pop();
                continue;
            }
            // next one is another, redo this thread
            else{
                pop_one();
                redo = true;
                break;
            }
        }

        if(redo == true)
            continue;

        shared_stack.finish_num++;

        // finish and pop next customer, except all finish
        if(shared_stack.finish_num < customer_num)
            pop_one();

        pthread_exit(NULL);
    }
}

int format_num(char ch[]){
    int num = 0;
    for(unsigned int i = 0; i < strlen(ch); i++)
        num = 10 * num + (ch[i] - 48);
    return num;
}
