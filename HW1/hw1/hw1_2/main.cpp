#include <iostream>
#include <fstream>
#include <stdio.h>
#include <string.h>
#include <cstdlib>
#include <pthread.h>
#include <queue>
#include <string>

#define _ ios::sync_with_stdio(0); cin.tie(0);

using namespace std;

struct Customer{
	int cid;
	int arrive_time;
    int play_round;
    int rest_time;
    int total_play_round;
    bool is_finish;
}*customer;

struct Shared_Stack{
	pthread_mutex_t	mutex;
	int timer;
    int guarantee_num;
    int guarantee_round;
    bool available_1;
    bool available_2;
    int finish_num;
    bool finish_buffer_1;
    bool finish_buffer_2;
    string finish_text_1;
    string finish_text_2;
}shared_stack;

struct Buffer{
    int cid;
    int round;   
}buffer_1, buffer_2;

int customer_num;
void init(void);
void *machine_1(void *param);
void *machine_2(void *param);
void push_to_queue(void);
int pop_one(void);
void check_available(void);
void check_wait(int status_1, int status_2);
int format_num(char ch[]);
queue<int> q_line;

int main(int argc, char *argv[]){
    FILE *file;
    char str[20];
    int idle = 0;
    init();

    // read file
    file = fopen(argv[1], "r");
    if(file == NULL)
        cout << "file open fail!" << endl;
    else{
        fscanf(file, "%s", str);
        shared_stack.guarantee_num = format_num(str);
        shared_stack.guarantee_round = shared_stack.guarantee_num;
        fscanf(file, "%s", str);
        customer_num = format_num(str);
        customer = new Customer[customer_num+1];

        for(int i = 1; i <= customer_num; i++){
            customer[i].cid = i;
            customer[i].is_finish = false;
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

    pthread_t tid_1;
    pthread_t tid_2;
    (void) pthread_mutex_init(&shared_stack.mutex, NULL);

    int need_wait = 0; // for many people in the first time
    for(int i = 1; i <= customer_num; i++){
        if(need_wait < 2 && customer[i].arrive_time == 0){
            q_line.push(i);
            need_wait++;
        }
        else if(need_wait == 2 && customer[i].arrive_time == 0){
            q_line.push(i);
            printf("%d %d wait in line\n", shared_stack.timer, i);
        }
    }

    int status_1 = 0;
    int status_2 = 0;
    while(1){
        check_available();
        if(shared_stack.available_1 == true && !q_line.empty()){
            int cid = pop_one();
            pthread_create(&tid_1, NULL, machine_1, &cid);
        }
        else if(shared_stack.available_1 == true && q_line.empty()){
            // do nothing, machine idle
            idle++;
            status_1 = 1;
        }
        else if(shared_stack.available_1 == false){
            pthread_create(&tid_1, NULL, machine_1, &buffer_1.cid);
        }

        if(shared_stack.available_2 == true && !q_line.empty()){
            int cid = pop_one();
            pthread_create(&tid_2, NULL, machine_2, &cid);        
        }
        else if(shared_stack.available_2 == true && q_line.empty()){
            // do nothing, machine idle
            idle++;
            status_2 = 1;
        }
        else if(shared_stack.available_2 == false){
            pthread_create(&tid_2, NULL, machine_2, &buffer_2.cid);
        }

        // check wait in line
        check_wait(status_1, status_2);
        
        // wait all thread to be done
        if(status_1 == 1){
            // no thread to wait 
        }
        else pthread_join(tid_1, NULL);
        if(status_2 == 1){
            // no thread to wait
        }
        else pthread_join(tid_2, NULL);

        if(shared_stack.finish_buffer_1 == true){
            cout << shared_stack.finish_text_1 << endl;
            shared_stack.finish_text_1[0] = '\0';
            shared_stack.finish_buffer_1 = false;
        }
        if(shared_stack.finish_buffer_2 == true){
            cout << shared_stack.finish_text_2 << endl;
            shared_stack.finish_text_2[0] = '\0';
            shared_stack.finish_buffer_2 = false;
        }

        // all finish
        if(shared_stack.finish_num == customer_num)
            break;
        
        if(idle == 2) // two machines idle, reset
            shared_stack.guarantee_round = shared_stack.guarantee_num;

        idle = 0;
        status_1 = 0;
        status_2 = 0;
        shared_stack.timer++;
        push_to_queue();
    }

    return 0;
}

void *machine_1(void *param){
 
    int cid = *(int *)param;
    if(buffer_1.cid == 0){
        buffer_1.cid = cid; // new customer
        printf("%d %d start playing #1\n", shared_stack.timer, cid);
    }   
    
    (void) pthread_mutex_lock(&shared_stack.mutex);

    buffer_1.round++;
    
    if(shared_stack.guarantee_round == 1 || buffer_1.round == customer[cid].total_play_round){ 
        // FINISH, when reach guarantee num OR reach customer total play round
        customer[cid].is_finish = true;
        shared_stack.guarantee_round = shared_stack.guarantee_num;
        buffer_1.cid = 0;
        buffer_1.round = 0;
        shared_stack.finish_num++;
        shared_stack.finish_buffer_1 = true;
        shared_stack.finish_text_1 = (to_string(shared_stack.timer+1) + " " + to_string(cid)) + " finishing playing YES #1";
        // printf("%d %d finishing playing YES #1\n", shared_stack.timer+1, cid);
    }
    else if(buffer_1.round == customer[cid].play_round){
        // REST, update arrive time, total play round, guarantee and clean buffer
        customer[cid].arrive_time = shared_stack.timer+1 + customer[cid].rest_time;
        customer[cid].total_play_round -= buffer_1.round;
        shared_stack.guarantee_round--;
        buffer_1.cid = 0;
        buffer_1.round = 0;
        shared_stack.finish_buffer_1 = true;
        shared_stack.finish_text_1 = (to_string(shared_stack.timer+1) + " " + to_string(cid)) + " finishing playing NO #1";
        //printf("%d %d finishing playing NO #1\n", shared_stack.timer+1, cid);
    }else{
        // KEEP PLAY, update guarantee
        shared_stack.guarantee_round--;
    }
    (void) pthread_mutex_unlock(&shared_stack.mutex);

    pthread_exit(NULL);
}

void *machine_2(void *param){

    int cid = *(int *)param;
    if(buffer_2.cid == 0){
        buffer_2.cid = cid; // new customer
        printf("%d %d start playing #2\n", shared_stack.timer, cid);
    }

    (void) pthread_mutex_lock(&shared_stack.mutex);

    buffer_2.round++;    
    
    if(shared_stack.guarantee_round == 1 || buffer_2.round == customer[cid].total_play_round){ 
        // FINISH, when reach guarantee num OR reach customer total play round
        customer[cid].is_finish = true;
        shared_stack.guarantee_round = shared_stack.guarantee_num;
        buffer_2.cid = 0;
        buffer_2.round = 0;
        shared_stack.finish_num++;
        shared_stack.finish_buffer_2 = true;
        shared_stack.finish_text_2 = (to_string(shared_stack.timer+1) + " " + to_string(cid)) + " finishing playing YES #2";
        // printf("%d %d finishing playing YES #2\n", shared_stack.timer+1, cid);
    }
    else if(buffer_2.round == customer[cid].play_round){
        // REST, update arrive time, total play round, guarantee and clean buffer
        customer[cid].arrive_time = shared_stack.timer+1 + customer[cid].rest_time;
        customer[cid].total_play_round -= buffer_2.round;
        shared_stack.guarantee_round--;
        buffer_2.cid = 0;
        buffer_2.round = 0;
        shared_stack.finish_buffer_2 = true;
        shared_stack.finish_text_2 = (to_string(shared_stack.timer+1) + " " + to_string(cid)) + " finishing playing NO #2";
        // printf("%d %d finishing playing NO #2\n", shared_stack.timer+1, cid);
    }else{
        // KEEP PLAY, update guarantee
        shared_stack.guarantee_round--;
    }
    (void) pthread_mutex_unlock(&shared_stack.mutex);

    pthread_exit(NULL);
}

void push_to_queue(void){
    for(int i = 1; i <= customer_num; i++){
        if(!customer[i].is_finish && customer[i].arrive_time == shared_stack.timer){
            q_line.push(i);
        }
    }
}

int pop_one(void){
    // pop one
    int cid = q_line.front();
    q_line.pop();
    return cid;
}

void check_available(void){
    if(buffer_1.cid != 0)
        shared_stack.available_1 = false;
    else
        shared_stack.available_1 = true;
    if(buffer_2.cid != 0)
        shared_stack.available_2 = false;
    else
        shared_stack.available_2 = true;
}

void check_wait(int status_1, int status_2){
    if(status_1 == 0 && status_2 == 0){
        queue<int> q_copy = q_line;
        while(!q_copy.empty()){
            int q_cid = q_copy.front();
            printf("%d %d wait in line\n", shared_stack.timer, q_cid);
            q_copy.pop();
        }
    }
}

void init(void){
    shared_stack.timer = 0;
    shared_stack.available_1 = true;
    shared_stack.available_2 = true;
    shared_stack.finish_num = 0;
    shared_stack.finish_buffer_1 = false;
    shared_stack.finish_buffer_2 = false;
    shared_stack.finish_text_1[0] = '\0';
    shared_stack.finish_text_2[0] = '\0';
    buffer_1.cid = 0;
    buffer_1.round = 0;
    buffer_2.cid = 0;
    buffer_2.round = 0;    
}

int format_num(char ch[]){
    int num = 0;
    for(unsigned int i = 0; i < strlen(ch); i++)
        num = 10 * num + (ch[i] - 48);
    return num;
}
