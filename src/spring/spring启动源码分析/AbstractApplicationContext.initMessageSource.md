## 简述
初始化MessageSource，用于支持国际化（i18n）消息。

这是refresh()方法的第7步，在BeanFactory后置处理和BeanPostProcessor注册之后执行。

MessageSource提供了解析消息的能力，支持参数化和国际化。

## 核心流程
1. 检查BeanFactory中是否已有名为"messageSource"的Bean
2. 如果有，直接使用
3. 如果没有，创建默认的DelegatingMessageSource
4. 将MessageSource注册为单例Bean

## 源码分析

```java
public abstract class AbstractApplicationContext extends DefaultResourceLoader
        implements ConfigurableApplicationContext {

    /** MessageSource的Bean名称 */
    public static final String MESSAGE_SOURCE_BEAN_NAME = "messageSource";

    /** MessageSource实例 */
    private MessageSource messageSource;

    @Override
    public void refresh() throws BeansException, IllegalStateException {
        synchronized (this.startupShutdownMonitor) {
            // ... 前面的步骤
            
            try {
                // ... invokeBeanFactoryPostProcessors
                // ... registerBeanPostProcessors
                
                // 初始化MessageSource
                initMessageSource();
                
                // ... 后续步骤
            }
            catch (BeansException ex) {
                // 异常处理
            }
        }
    }

    protected void initMessageSource() {
        ConfigurableListableBeanFactory beanFactory = getBeanFactory();
        
        // 检查是否已有messageSource Bean
        if (beanFactory.containsLocalBean(MESSAGE_SOURCE_BEAN_NAME)) {
            // 如果有，获取并使用
            this.messageSource = beanFactory.getBean(MESSAGE_SOURCE_BEAN_NAME, MessageSource.class);
            
            // 如果父上下文也是MessageSource，设置父MessageSource
            if (this.parent != null && this.messageSource instanceof HierarchicalMessageSource) {
                HierarchicalMessageSource hms = (HierarchicalMessageSource) this.messageSource;
                if (hms.getParentMessageSource() == null) {
                    // 只有当前MessageSource还没有父MessageSource时才设置
                    hms.setParentMessageSource(getInternalParentMessageSource());
                }
            }
            
            if (logger.isTraceEnabled()) {
                logger.trace("Using MessageSource [" + this.messageSource + "]");
            }
        }
        else {
            // 如果没有，创建默认的DelegatingMessageSource
            DelegatingMessageSource dms = new DelegatingMessageSource();
            dms.setParentMessageSource(getInternalParentMessageSource());
            this.messageSource = dms;
            
            // 注册为单例Bean
            beanFactory.registerSingleton(MESSAGE_SOURCE_BEAN_NAME, this.messageSource);
            
            if (logger.isTraceEnabled()) {
                logger.trace("No '" + MESSAGE_SOURCE_BEAN_NAME + "' bean, using [" + this.messageSource + "]");
            }
        }
    }

    @Nullable
    protected MessageSource getInternalParentMessageSource() {
        return (getParent() instanceof AbstractApplicationContext ?
                ((AbstractApplicationContext) getParent()).messageSource : getParent());
    }
}
```

## MessageSource接口

```java
public interface MessageSource {
    
    /**
     * 解析消息
     * @param code 消息代码
     * @param args 消息参数（用于占位符）
     * @param defaultMessage 默认消息
     * @param locale 区域设置
     */
    @Nullable
    String getMessage(String code, @Nullable Object[] args, 
                      @Nullable String defaultMessage, Locale locale);

    /**
     * 解析消息（必须存在，否则抛出异常）
     */
    String getMessage(String code, @Nullable Object[] args, Locale locale)
            throws NoSuchMessageException;

    /**
     * 解析消息（使用MessageSourceResolvable）
     */
    String getMessage(MessageSourceResolvable resolvable, Locale locale)
            throws NoSuchMessageException;
}
```

## DelegatingMessageSource

默认的MessageSource实现，简单地委托给父MessageSource：

```java
public class DelegatingMessageSource extends MessageSourceSupport 
        implements HierarchicalMessageSource {

    @Nullable
    private MessageSource parentMessageSource;

    @Override
    @Nullable
    public String getMessage(String code, @Nullable Object[] args, 
                             @Nullable String defaultMessage, Locale locale) {
        if (this.parentMessageSource != null) {
            return this.parentMessageSource.getMessage(code, args, defaultMessage, locale);
        }
        else if (defaultMessage != null) {
            return renderDefaultMessage(defaultMessage, args, locale);
        }
        else {
            return null;
        }
    }
}
```

如果没有配置MessageSource且没有父上下文，DelegatingMessageSource会简单地返回null或默认消息。

## 自定义MessageSource

在SpringBoot应用中，通常使用ResourceBundleMessageSource或ReloadableResourceBundleMessageSource：

```java
@Configuration
public class MessageSourceConfig {

    @Bean
    public MessageSource messageSource() {
        ResourceBundleMessageSource messageSource = new ResourceBundleMessageSource();
        
        // 设置消息文件的基础名称（不包含语言代码和.properties）
        messageSource.setBasenames("messages", "validation");
        
        // 设置默认编码
        messageSource.setDefaultEncoding("UTF-8");
        
        // 设置缓存时间（秒），-1表示永久缓存
        messageSource.setCacheSeconds(3600);
        
        // 设置是否使用系统区域设置作为默认
        messageSource.setFallbackToSystemLocale(false);
        
        return messageSource;
    }
}
```

SpringBoot自动配置：
```java
@Bean
@ConditionalOnMissingBean
public MessageSource messageSource(MessageSourceProperties properties) {
    ResourceBundleMessageSource messageSource = new ResourceBundleMessageSource();
    if (StringUtils.hasText(properties.getBasename())) {
        messageSource.setBasenames(
            StringUtils.commaDelimitedListToStringArray(
                StringUtils.trimAllWhitespace(properties.getBasename())));
    }
    messageSource.setDefaultEncoding(properties.getEncoding().name());
    messageSource.setCacheSeconds((int) properties.getCacheDuration().getSeconds());
    messageSource.setFallbackToSystemLocale(properties.isFallbackToSystemLocale());
    messageSource.setAlwaysUseMessageFormat(properties.isAlwaysUseMessageFormat());
    messageSource.setUseCodeAsDefaultMessage(properties.isUseCodeAsDefaultMessage());
    return messageSource;
}
```

## 消息文件示例

**messages.properties（默认）：**
```properties
welcome.message=Welcome to our application
user.greeting=Hello, {0}!
error.notfound=Resource not found
```

**messages_zh_CN.properties（中文）：**
```properties
welcome.message=欢迎使用我们的应用
user.greeting=你好，{0}！
error.notfound=资源未找到
```

**messages_en_US.properties（英文）：**
```properties
welcome.message=Welcome to our application
user.greeting=Hello, {0}!
error.notfound=Resource not found
```

## 使用MessageSource

### 1. 通过ApplicationContext

```java
@Component
public class MyService {
    
    @Autowired
    private ApplicationContext context;
    
    public void doSomething() {
        // 获取消息（使用当前Locale）
        String message = context.getMessage("welcome.message", null, LocaleContextHolder.getLocale());
        
        // 带参数的消息
        String greeting = context.getMessage("user.greeting", new Object[]{"张三"}, Locale.CHINA);
        // 输出：你好，张三！
    }
}
```

### 2. 直接注入MessageSource

```java
@Component
public class MyService {
    
    @Autowired
    private MessageSource messageSource;
    
    public void doSomething() {
        String message = messageSource.getMessage("welcome.message", null, 
                                                  LocaleContextHolder.getLocale());
    }
}
```

### 3. 在Controller中使用

```java
@RestController
public class MyController {
    
    @Autowired
    private MessageSource messageSource;
    
    @GetMapping("/greeting")
    public String greeting(@RequestParam String name, Locale locale) {
        return messageSource.getMessage("user.greeting", new Object[]{name}, locale);
    }
}
```

### 4. 在视图模板中使用

Thymeleaf示例：
```html
<!-- 使用th:text -->
<p th:text="#{welcome.message}">Default welcome message</p>

<!-- 带参数 -->
<p th:text="#{user.greeting(${userName})}">Hello</p>
```

## MessageSource的层级结构

ApplicationContext可以有父子关系，MessageSource也支持层级结构：

```
Parent ApplicationContext (messageSource1)
  └── Child ApplicationContext (messageSource2)
```

子上下文的MessageSource查找顺序：
1. 先在子MessageSource中查找
2. 如果找不到，在父MessageSource中查找
3. 如果还找不到，返回默认消息或抛出异常

## SpringBoot配置

application.properties：
```properties
# 消息文件基础名称（默认是messages）
spring.messages.basename=messages,config.i18n.messages

# 编码格式
spring.messages.encoding=UTF-8

# 缓存时间（秒），-1表示永久缓存，开发环境可以设置为0
spring.messages.cache-duration=3600

# 找不到对应语言的消息时，是否回退到系统Locale
spring.messages.fallback-to-system-locale=true

# 消息代码不存在时，是否使用代码作为默认消息
spring.messages.use-code-as-default-message=false
```

## 参考调用栈

```text
initMessageSource:857, AbstractApplicationContext (org.springframework.context.support)
refresh:538, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
```

## 相关链接
- [Spring官方文档 - Internationalization](https://docs.spring.io/spring-framework/docs/current/reference/html/core.html#context-functionality-messagesource)

